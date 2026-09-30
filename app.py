import io
import os
import re
import time
import uuid
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
except ImportError:
    A4 = None


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
DATABASE_PATH = BASE_DIR / "agrin_history.db"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_UPLOAD_SIZE = 8 * 1024 * 1024
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_RETRY_ATTEMPTS = 3

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "change-this-secret-key-before-production"),
    DATABASE=str(DATABASE_PATH),
    UPLOAD_FOLDER=str(UPLOAD_FOLDER),
    MAX_CONTENT_LENGTH=MAX_UPLOAD_SIZE,
)


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'English',
            ui_language TEXT NOT NULL DEFAULT 'en',
            notes TEXT DEFAULT '',
            diagnosis TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.commit()
    db.close()


def save_diagnosis(
    image_filename,
    original_filename,
    language,
    ui_language,
    notes,
    diagnosis,
):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO diagnoses (
            image_filename,
            original_filename,
            language,
            ui_language,
            notes,
            diagnosis,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            image_filename,
            original_filename,
            language,
            ui_language,
            notes,
            diagnosis,
            utc_now(),
        ),
    )
    db.commit()
    return cursor.lastrowid


def get_diagnosis_or_404(diagnosis_id):
    record = get_db().execute(
        "SELECT * FROM diagnoses WHERE id = ?",
        (diagnosis_id,),
    ).fetchone()

    if record is None:
        abort(404)

    return record


def extract_status(diagnosis_text):
    text = diagnosis_text.lower()

    healthy_words = [
        "healthy",
        "no disease",
        "no visible disease",
        "no obvious disease",
        "no significant disease",
    ]
    urgent_words = [
        "urgent",
        "severe",
        "critical",
        "immediately",
        "rapidly spreading",
    ]

    if any(word in text for word in urgent_words):
        return "Needs urgent attention"

    if any(word in text for word in healthy_words):
        return "Likely healthy"

    return "Possible plant issue"


def build_prompt(language, notes):
    extra_notes = notes.strip() if notes else "No additional farmer notes were provided."

    return f"""
You are CropCare Sathi, a careful agricultural crop-health assistant.

Analyze the supplied crop or plant image. Respond in {language}.
Use simple, farmer-friendly language. Do not claim certainty from an image alone.
If image quality or plant visibility is insufficient, say so clearly and explain what
additional photograph or information is needed.

Farmer notes:
{extra_notes}

Use exactly these headings:

Plant / crop observed
Visible symptoms
Likely condition
Confidence
What may be causing it
Recommended next steps
Prevention
When to contact a local agriculture expert

Safety rules:
- Clearly distinguish observations from possible diagnoses.
- Do not invent pesticide doses, brand names, or chemical concentrations.
- Prefer low-risk integrated pest-management actions first.
- Mention that treatment choices must follow local labels, local regulations,
  crop stage, and advice from a qualified agricultural professional.
- If the plant looks severely affected, state that the farmer should seek local
  agricultural-extension or plant-pathology advice promptly.
""".strip()


def diagnose_with_gemini(image_bytes, mime_type, language, notes):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if genai is None or types is None:
        raise RuntimeError(
            "Gemini SDK is unavailable. Install the google-genai package first."
        )

    if not api_key:
        raise RuntimeError(
            "Gemini API key is missing. Set GEMINI_API_KEY in your environment."
        )

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(language, notes)
    last_error = None

    for attempt in range(1, GEMINI_RETRY_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
            )

            result = (getattr(response, "text", None) or "").strip()

            if not result:
                raise RuntimeError(
                    "Gemini returned an empty response. Please try again."
                )

            return result

        except Exception as error:
            last_error = error

            if attempt < GEMINI_RETRY_ATTEMPTS:
                time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        "The diagnosis service could not respond after several attempts. "
        f"Please try again shortly. Details: {last_error}"
    )


def safe_pdf_text(value):
    value = value or ""
    value = value.replace("\x00", "")
    return value.encode("latin-1", "replace").decode("latin-1")


def diagnosis_to_pdf(record):
    if A4 is None:
        raise RuntimeError(
            "PDF support is unavailable. Install reportlab to enable downloads."
        )

    pdf_buffer = io.BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"AgriN Diagnosis #{record['id']}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AgriNTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        spaceAfter=12,
        textColor="#1B5E20",
    )
    heading_style = ParagraphStyle(
        "AgriNHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=5,
        textColor="#1B5E20",
    )
    body_style = ParagraphStyle(
        "AgriNBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )

    diagnosis_html = safe_pdf_text(record["diagnosis"])
    diagnosis_html = diagnosis_html.replace("&", "&amp;")
    diagnosis_html = diagnosis_html.replace("<", "&lt;")
    diagnosis_html = diagnosis_html.replace(">", "&gt;")
    diagnosis_html = diagnosis_html.replace("\n", "<br/>")

    notes = safe_pdf_text(record["notes"] or "No additional notes supplied.")
    notes = notes.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    story = [
        Paragraph("CropCare Sathi Diagnosis Report", title_style),
        Paragraph(f"<b>Report ID:</b> #{record['id']}", body_style),
        Paragraph(f"<b>Created:</b> {safe_pdf_text(record['created_at'])}", body_style),
        Paragraph(
            f"<b>Image:</b> {safe_pdf_text(record['original_filename'])}",
            body_style,
        ),
        Paragraph(
            f"<b>Requested diagnosis language:</b> {safe_pdf_text(record['language'])}",
            body_style,
        ),
        Spacer(1, 8),
        Paragraph("Farmer notes", heading_style),
        Paragraph(notes, body_style),
        Paragraph("Diagnosis", heading_style),
        Paragraph(diagnosis_html, body_style),
        Spacer(1, 10),
        Paragraph(
            "Important: This image-based result is informational and may not be a "
            "definitive diagnosis. Confirm serious crop problems with a local "
            "agriculture officer, extension worker, or qualified plant expert.",
            body_style,
        ),
    ]

    document.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer


@app.errorhandler(413)
def file_too_large(error):
    flash(
        f"Image is too large. Please upload an image smaller than "
        f"{MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
        "error",
    )
    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    image = request.files.get("image")
    language = (request.form.get("language") or "English").strip()
    notes = (request.form.get("notes") or "").strip()
    ui_language = (request.form.get("ui_lang") or "en").strip()

    if image is None or image.filename == "":
        flash("Please select a plant or crop image before submitting.", "error")
        return redirect(url_for("index"))

    if not allowed_file(image.filename):
        flash("Use a PNG, JPG, JPEG, or WEBP image file.", "error")
        return redirect(url_for("index"))

    if image.mimetype not in ALLOWED_MIME_TYPES:
        flash("The uploaded file does not appear to be a supported image.", "error")
        return redirect(url_for("index"))

    image_bytes = image.read()

    if not image_bytes:
        flash("The uploaded image file is empty.", "error")
        return redirect(url_for("index"))

    if len(image_bytes) > MAX_UPLOAD_SIZE:
        flash(
            f"Image is too large. Please upload an image smaller than "
            f"{MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
            "error",
        )
        return redirect(url_for("index"))

    original_filename = secure_filename(image.filename) or "plant-image"
    extension = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{extension}"
    image_path = UPLOAD_FOLDER / stored_filename

    try:
        image_path.write_bytes(image_bytes)
        diagnosis = diagnose_with_gemini(
            image_bytes=image_bytes,
            mime_type=image.mimetype,
            language=language,
            notes=notes,
        )

        diagnosis_id = save_diagnosis(
            image_filename=stored_filename,
            original_filename=original_filename,
            language=language,
            ui_language=ui_language,
            notes=notes,
            diagnosis=diagnosis,
        )

        return redirect(url_for("diagnosis_detail", diagnosis_id=diagnosis_id))

    except Exception as error:
        if image_path.exists():
            image_path.unlink()

        flash(str(error), "error")
        return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    db = get_db()

    total_diagnoses = db.execute(
        "SELECT COUNT(*) AS total FROM diagnoses"
    ).fetchone()["total"]

    recent_diagnoses = db.execute(
        """
        SELECT id, image_filename, original_filename, language, diagnosis, created_at
        FROM diagnoses
        ORDER BY id DESC
        LIMIT 5
        """
    ).fetchall()

    all_diagnoses = db.execute(
        "SELECT diagnosis FROM diagnoses ORDER BY id DESC"
    ).fetchall()

    status_counts = {
        "Likely healthy": 0,
        "Possible plant issue": 0,
        "Needs urgent attention": 0,
    }

    for row in all_diagnoses:
        status_counts[extract_status(row["diagnosis"])] += 1

    return render_template(
        "dashboard.html",
        total_diagnoses=total_diagnoses,
        recent_diagnoses=recent_diagnoses,
        status_counts=status_counts,
    )


@app.route("/diagnosis/<int:diagnosis_id>")
def diagnosis_detail(diagnosis_id):
    record = get_diagnosis_or_404(diagnosis_id)

    return render_template(
        "index.html",
        record=record,
        diagnosis=record["diagnosis"],
        diagnosis_status=extract_status(record["diagnosis"]),
        uploaded_image_url=url_for("uploaded_file", filename=record["image_filename"]),
    )


@app.route("/history")
def history():
    search = (request.args.get("q") or "").strip()
    db = get_db()

    if search:
        records = db.execute(
            """
            SELECT *
            FROM diagnoses
            WHERE original_filename LIKE ?
               OR diagnosis LIKE ?
               OR notes LIKE ?
               OR language LIKE ?
            ORDER BY id DESC
            """,
            (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        records = db.execute(
            "SELECT * FROM diagnoses ORDER BY id DESC"
        ).fetchall()

    return render_template(
        "history.html",
        records=records,
        search=search,
    )


@app.route("/history/<int:diagnosis_id>")
def history_detail(diagnosis_id):
    record = get_diagnosis_or_404(diagnosis_id)

    return render_template(
        "history_detail.html",
        record=record,
        diagnosis_status=extract_status(record["diagnosis"]),
        uploaded_image_url=url_for(
            "uploaded_file",
            filename=record["image_filename"]
        ),
    )

@app.route("/knowledge")
def knowledge():
    knowledge_items = [
        {
            "title": "Take a useful crop photo",
            "content": (
                "Use daylight, keep the affected leaf or plant in focus, and include "
                "both close and wider views when possible. Avoid blurry images."
            ),
        },
        {
            "title": "Check both sides of leaves",
            "content": (
                "Many pests, eggs, fungal growth, and leaf spots are easier to see on "
                "the underside of leaves."
            ),
        },
        {
            "title": "Separate observation from diagnosis",
            "content": (
                "Yellowing, spots, curling, or wilting can have several causes. Check "
                "watering, nutrient conditions, weather, pests, and disease signs."
            ),
        },
        {
            "title": "Use integrated pest management",
            "content": (
                "Start with field sanitation, removal of severely affected plant parts, "
                "monitoring, resistant varieties where available, and locally approved guidance."
            ),
        },
        {
            "title": "Seek local help for severe cases",
            "content": (
                "Rapid spread, major crop loss, or unusual symptoms should be checked "
                "by a local agriculture officer, extension worker, or plant expert."
            ),
        },
    ]

    return render_template(
        "knowledge.html",
        knowledge_items=knowledge_items,
    )


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/download/<int:diagnosis_id>")
def download_pdf(diagnosis_id):
    record = get_diagnosis_or_404(diagnosis_id)

    try:
        pdf_buffer = diagnosis_to_pdf(record)
    except RuntimeError as error:
        flash(str(error), "error")
        return redirect(url_for("history_detail", diagnosis_id=diagnosis_id))

    download_name = f"CropCare Sathi Diagnosis-{diagnosis_id}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=download_name,
    )


@app.context_processor
def inject_template_utilities():
    return {
        "current_year": datetime.now().year,
        "diagnosis_status": extract_status,
    }

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080, debug=True)