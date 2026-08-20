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
from flask import Flask, request, render_template
import google.generativeai as genai
from PIL import Image

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
  "regenerative_steps": ["low-cost, regenerative-agriculture-aligned step 1", "step 2", "step 3"]
}}

Severity guide:
- "low": plant appears healthy, or only very minor/cosmetic issue, no urgent action needed
- "medium": a real issue is present that should be addressed soon to prevent spread or worsening
- "high": a serious issue that risks significant crop loss if not acted on quickly

IMPORTANT: Write every text value in the JSON (diagnosis, confidence_note, regenerative_steps,
crop_guess) in {language}. Keep the JSON keys themselves in English exactly as shown above —
only the values should be translated. Use simple, clear language a farmer with no technical
background can understand.

Farmer's notes: {notes}
"""

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese (Simplified)",
    "af": "Afrikaans",
    "sw": "Swahili",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
}


@app.route("/", methods=["GET", "POST"])
def diagnose():
    result = None
    error = None
    notes = ""
    selected_lang = "en"

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
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)