"""
AgriN Crop Diagnosis & Advisory — MVP
Track: Sustainability/Resilience (AgriN) | Build with AI: Code for Communities

Setup:
  1. pip install flask google-generativeai pillow
  2. Get a free API key at https://aistudio.google.com
  3. export GEMINI_API_KEY="your-key-here"
  4. python app.py
  5. Open http://localhost:8080
"""

import os
import json
from flask import Flask, request, render_template, Response
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF

# --- Config ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY environment variable first.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-3.6-flash")

app = Flask(__name__)

DIAGNOSIS_PROMPT = """You are an agricultural advisor helping a smallholder farmer who has
limited access to expert consultation. Analyze the crop image below (and any notes provided)
and respond ONLY in this exact JSON format, no extra text, no markdown fences:

{{
  "crop_guess": "likely crop type, or 'unclear' if not identifiable",
  "diagnosis": "likely issue — disease, pest, nutrient deficiency, or 'appears healthy'",
  "severity": "low" | "medium" | "high",
  "confidence_note": "one honest sentence on certainty — recommend expert follow-up if unsure",
  "regenerative_steps": ["low-cost, regenerative-agriculture-aligned step 1", "step 2", "step 3"],
  "diagnosis_en": "same as 'diagnosis' but always in English",
  "confidence_note_en": "same as 'confidence_note' but always in English",
  "regenerative_steps_en": ["same as 'regenerative_steps' but always in English"]
}}

Severity guide:
- "low": plant appears healthy, or only very minor/cosmetic issue, no urgent action needed
- "medium": a real issue is present that should be addressed soon to prevent spread or worsening
- "high": a serious issue that risks significant crop loss if not acted on quickly

IMPORTANT: Write crop_guess, diagnosis, confidence_note, and regenerative_steps in {language}.
Write diagnosis_en, confidence_note_en, and regenerative_steps_en in English, always, regardless
of {language} — these are used for a downloadable report and must stay in English for
compatibility. Keep the JSON keys themselves in English exactly as shown above. Use simple,
clear language a farmer with no technical background can understand.

Farmer's notes: {notes}
"""

SUPPORTED_LANGUAGES = {
    "en": "English",
    # Indian regional languages
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    # BRICS + major world languages
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese (Simplified)",
    "af": "Afrikaans",
    "zu": "Zulu",
    "sw": "Swahili",
    "es": "Spanish",
    "fr": "French",
    "ar": "Arabic",
    "id": "Indonesian",
}

# UI text translations for the page shell (headings, buttons, labels).
# Not every language has a full UI translation yet — languages without one
# fall back to English for the interface text (the AI diagnosis itself still
# works in all SUPPORTED_LANGUAGES regardless of UI language).
UI_STRINGS = {
    "en": {
        "title": "AgriN Crop Advisor",
        "subtitle": "Upload a photo of your crop for an instant AI diagnosis and regenerative treatment advice — built for smallholder farmers across BRICS nations.",
        "upload_hint": "Tap to upload a photo",
        "upload_hint_small": "Leaf, stem, or affected area works best",
        "language_label": "Response language",
        "notes_label": "Any notes? (optional)",
        "notes_placeholder": "e.g. leaves turning yellow for a week, seen after heavy rain...",
        "submit_button": "Diagnose Crop",
        "loading_text": "Analyzing your crop photo...",
        "recommended_steps": "Recommended Steps",
        "urgency_suffix": "urgency",
        "pdf_button": "Download PDF Report (English)",
        "footer": "Built for Build with AI: Code for Communities — AgriN Track · Powered by Gemini",
    },
    "hi": {
        "title": "एग्रीएन फसल सलाहकार",
        "subtitle": "तुरंत एआई निदान और पुनर्योजी उपचार सलाह के लिए अपनी फसल की फोटो अपलोड करें — ब्रिक्स देशों के छोटे किसानों के लिए बनाया गया।",
        "upload_hint": "फोटो अपलोड करने के लिए टैप करें",
        "upload_hint_small": "पत्ती, तना, या प्रभावित हिस्सा सबसे अच्छा काम करता है",
        "language_label": "उत्तर की भाषा",
        "notes_label": "कोई टिप्पणी? (वैकल्पिक)",
        "notes_placeholder": "जैसे: एक सप्ताह से पत्तियां पीली हो रही हैं, तेज़ बारिश के बाद देखा गया...",
        "submit_button": "फसल की जांच करें",
        "loading_text": "आपकी फसल की फोटो का विश्लेषण हो रहा है...",
        "recommended_steps": "सुझाए गए कदम",
        "urgency_suffix": "तात्कालिकता",
        "pdf_button": "पीडीएफ रिपोर्ट डाउनलोड करें (अंग्रेज़ी में)",
        "footer": "Build with AI: Code for Communities — AgriN ट्रैक के लिए बनाया गया · Gemini द्वारा संचालित",
    },
    "pt": {
        "title": "Consultor Agrícola AgriN",
        "subtitle": "Envie uma foto da sua plantação para um diagnóstico instantâneo por IA e conselhos de tratamento regenerativo — feito para pequenos agricultores dos países do BRICS.",
        "upload_hint": "Toque para enviar uma foto",
        "upload_hint_small": "Folha, caule ou área afetada funciona melhor",
        "language_label": "Idioma da resposta",
        "notes_label": "Alguma observação? (opcional)",
        "notes_placeholder": "ex: folhas amarelando há uma semana, visto após chuva forte...",
        "submit_button": "Diagnosticar Plantação",
        "loading_text": "Analisando a foto da sua plantação...",
        "recommended_steps": "Passos Recomendados",
        "urgency_suffix": "urgência",
        "pdf_button": "Baixar Relatório em PDF (Inglês)",
        "footer": "Feito para Build with AI: Code for Communities — Trilha AgriN · Desenvolvido com Gemini",
    },
    "es": {
        "title": "Asesor de Cultivos AgriN",
        "subtitle": "Sube una foto de tu cultivo para un diagnóstico instantáneo con IA y consejos de tratamiento regenerativo — creado para pequeños agricultores de las naciones BRICS.",
        "upload_hint": "Toca para subir una foto",
        "upload_hint_small": "Una hoja, tallo o área afectada funciona mejor",
        "language_label": "Idioma de respuesta",
        "notes_label": "¿Alguna nota? (opcional)",
        "notes_placeholder": "ej: hojas amarillentas desde hace una semana, visto tras lluvia fuerte...",
        "submit_button": "Diagnosticar Cultivo",
        "loading_text": "Analizando la foto de tu cultivo...",
        "recommended_steps": "Pasos Recomendados",
        "urgency_suffix": "urgencia",
        "pdf_button": "Descargar Informe PDF (Inglés)",
        "footer": "Creado para Build with AI: Code for Communities — Categoría AgriN · Impulsado por Gemini",
    },
    "fr": {
        "title": "Conseiller Agricole AgriN",
        "subtitle": "Téléchargez une photo de votre culture pour un diagnostic IA instantané et des conseils de traitement régénératif — conçu pour les petits agriculteurs des nations BRICS.",
        "upload_hint": "Touchez pour télécharger une photo",
        "upload_hint_small": "Une feuille, une tige ou une zone affectée fonctionne mieux",
        "language_label": "Langue de réponse",
        "notes_label": "Des notes? (facultatif)",
        "notes_placeholder": "ex: feuilles jaunissantes depuis une semaine, observé après de fortes pluies...",
        "submit_button": "Diagnostiquer la Culture",
        "loading_text": "Analyse de la photo de votre culture...",
        "recommended_steps": "Étapes Recommandées",
        "urgency_suffix": "urgence",
        "pdf_button": "Télécharger le Rapport PDF (Anglais)",
        "footer": "Conçu pour Build with AI: Code for Communities — Catégorie AgriN · Propulsé par Gemini",
    },
    "ru": {
        "title": "Агроконсультант AgriN",
        "subtitle": "Загрузите фото вашей культуры для мгновенной диагностики ИИ и рекомендаций по регенеративному лечению — создано для мелких фермеров стран БРИКС.",
        "upload_hint": "Нажмите, чтобы загрузить фото",
        "upload_hint_small": "Лучше всего подходит лист, стебель или поражённый участок",
        "language_label": "Язык ответа",
        "notes_label": "Есть заметки? (необязательно)",
        "notes_placeholder": "напр.: листья желтеют неделю, замечено после сильного дождя...",
        "submit_button": "Диагностировать Культуру",
        "loading_text": "Анализ фото вашей культуры...",
        "recommended_steps": "Рекомендуемые Шаги",
        "urgency_suffix": "срочность",
        "pdf_button": "Скачать PDF-отчёт (на английском)",
        "footer": "Создано для Build with AI: Code for Communities — Направление AgriN · На основе Gemini",
    },
    "zh": {
        "title": "AgriN 作物顾问",
        "subtitle": "上传作物照片,获取即时 AI 诊断和再生治疗建议 — 专为金砖国家小农户打造。",
        "upload_hint": "点击上传照片",
        "upload_hint_small": "叶片、茎部或受影响区域效果最佳",
        "language_label": "回复语言",
        "notes_label": "备注(可选)",
        "notes_placeholder": "例如:叶片发黄一周,暴雨后发现...",
        "submit_button": "诊断作物",
        "loading_text": "正在分析您的作物照片...",
        "recommended_steps": "建议步骤",
        "urgency_suffix": "紧急程度",
        "pdf_button": "下载 PDF 报告(英文)",
        "footer": "为 Build with AI: Code for Communities — AgriN 赛道打造 · 由 Gemini 提供支持",
    },
    "ar": {
        "title": "مستشار المحاصيل AgriN",
        "subtitle": "قم بتحميل صورة لمحصولك للحصول على تشخيص فوري بالذكاء الاصطناعي ونصائح علاج تجديدية — مصمم لصغار المزارعين في دول البريكس.",
        "upload_hint": "اضغط لتحميل صورة",
        "upload_hint_small": "الورقة أو الساق أو المنطقة المصابة تعمل بشكل أفضل",
        "language_label": "لغة الرد",
        "notes_label": "أي ملاحظات؟ (اختياري)",
        "notes_placeholder": "مثال: الأوراق تصفرّ منذ أسبوع، لوحظ بعد مطر غزير...",
        "submit_button": "تشخيص المحصول",
        "loading_text": "جاري تحليل صورة محصولك...",
        "recommended_steps": "الخطوات الموصى بها",
        "urgency_suffix": "درجة الإلحاح",
        "pdf_button": "تحميل تقرير PDF (بالإنجليزية)",
        "footer": "تم إنشاؤه لبرنامج Build with AI: Code for Communities — مسار AgriN · بدعم من Gemini",
    },
}


def get_ui_strings(lang_code):
    return UI_STRINGS.get(lang_code, UI_STRINGS["en"])


@app.route("/", methods=["GET", "POST"])
def diagnose():
    result = None
    error = None
    notes = ""
    # UI language: controls page text (buttons, labels), set via top-right switcher
    ui_lang = request.args.get("ui_lang") or request.form.get("ui_lang", "en")
    # Diagnosis language: controls the AI's response language, set via the form dropdown
    selected_lang = request.args.get("lang", "en")

    if request.method == "POST":
        notes = request.form.get("notes", "").strip()
        selected_lang = request.form.get("language", "en")
        language_name = SUPPORTED_LANGUAGES.get(selected_lang, "English")
        image_file = request.files.get("image")

        if image_file:
            try:
                img = Image.open(image_file.stream)
                prompt = DIAGNOSIS_PROMPT.format(notes=notes or "none provided", language=language_name)
                response = model.generate_content([prompt, img])
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.strip("`").replace("json", "", 1).strip()
                result = json.loads(text)
            except Exception as e:
                error = f"Error analyzing image: {e}"

    return render_template(
        "index.html",
        result=result,
        error=error,
        notes=notes,
        languages=SUPPORTED_LANGUAGES,
        selected_lang=selected_lang,
        ui_lang=ui_lang,
        ui=get_ui_strings(ui_lang),
    )


def to_latin1_safe(text):
    """Strip any characters fpdf2's base font can't render, as a safety net."""
    return text.encode("latin-1", "replace").decode("latin-1")


@app.route("/download-pdf", methods=["POST"])
def download_pdf():
    crop = to_latin1_safe(request.form.get("crop_en", ""))
    diagnosis = to_latin1_safe(request.form.get("diagnosis_en", ""))
    severity = request.form.get("severity", "")
    confidence = to_latin1_safe(request.form.get("confidence_en", ""))
    steps_raw = request.form.get("steps_en", "[]")
    try:
        steps = [to_latin1_safe(s) for s in json.loads(steps_raw)]
    except Exception:
        steps = []

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(45, 106, 79)  # brand green
    pdf.cell(0, 12, "AgriN Crop Diagnosis Report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Build with AI: Code for Communities - AgriN Track", ln=True)
    pdf.ln(6)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Crop: {crop}", ln=True)
    pdf.cell(0, 8, f"Urgency: {severity.upper()}", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(0, 8, f"Diagnosis: {diagnosis}")
    pdf.ln(1)

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 6, confidence)
    pdf.ln(4)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Recommended Steps:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for step in steps:
        pdf.multi_cell(0, 7, f"- {step}")
    pdf.ln(6)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(140, 140, 140)
    pdf.multi_cell(0, 5, "This is an AI-generated preliminary assessment (shown here in English "
                          "for compatibility). Consult a local agricultural extension officer "
                          "for confirmation, especially for high-urgency cases.")

    pdf_bytes = bytes(pdf.output())
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=crop_diagnosis_report.pdf"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)