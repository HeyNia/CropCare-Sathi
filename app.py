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
from flask import Flask, request, render_template_string
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
  "confidence_note": "one honest sentence on certainty — recommend expert follow-up if unsure",
  "regenerative_steps": ["low-cost, regenerative-agriculture-aligned step 1", "step 2", "step 3"]
}}

Farmer's notes: {notes}
"""

PAGE = """
<!doctype html>
<html data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AgriN — Crop Diagnosis Advisor</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <style>
    body { max-width: 720px; margin: 0 auto; padding: 1rem; }
    header { text-align: center; margin-bottom: 1.5rem; }
    header h1 { margin-bottom: 0.25rem; color: #2d6a4f; }
    header p { color: var(--pico-muted-color); }
    .upload-card { border: 2px dashed #74c69d; border-radius: 12px; padding: 1.5rem; text-align: center; }
    .result-card { border-left: 4px solid #2d6a4f; padding: 1rem 1.25rem; margin-top: 1.5rem; }
    .badge { display: inline-block; background: #d8f3dc; color: #1b4332; padding: 0.2rem 0.7rem;
             border-radius: 999px; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; }
    footer { text-align: center; margin-top: 2rem; font-size: 0.8rem; color: var(--pico-muted-color); }
  </style>
</head>
<body>
  <header>
    <h1>🌱 AgriN Crop Advisor</h1>
    <p>Upload a photo of your crop for an instant diagnosis and regenerative treatment advice.</p>
  </header>

  <form method="POST" enctype="multipart/form-data">
    <div class="upload-card">
      <input type="file" name="image" accept="image/*" required>
      <p style="font-size:0.85rem; color:var(--pico-muted-color); margin-top:0.5rem;">
        Photo of a leaf, stem, or affected area works best.
      </p>
    </div>
    <label for="notes">Any notes? (optional)</label>
    <textarea id="notes" name="notes" rows="2"
      placeholder="e.g. leaves turning yellow for a week, seen after heavy rain...">{{notes or ""}}</textarea>
    <button type="submit">Diagnose Crop</button>
  </form>

  {% if result %}
  <article class="result-card">
    <span class="badge">{{result.crop_guess}}</span>
    <h3>{{result.diagnosis}}</h3>
    <p><em>{{result.confidence_note}}</em></p>
    <h4>Recommended steps</h4>
    <ul>
    {% for step in result.regenerative_steps %}
      <li>{{step}}</li>
    {% endfor %}
    </ul>
  </article>
  {% endif %}

  {% if error %}
    <p style="color:#c0392b;">{{error}}</p>
  {% endif %}

  <footer>Built for Build with AI: Code for Communities — AgriN Track</footer>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def diagnose():
    result = None
    error = None
    notes = ""

    if request.method == "POST":
        notes = request.form.get("notes", "").strip()
        image_file = request.files.get("image")

        if image_file:
            try:
                img = Image.open(image_file.stream)
                prompt = DIAGNOSIS_PROMPT.format(notes=notes or "none provided")
                response = model.generate_content([prompt, img])
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.strip("`").replace("json", "", 1).strip()
                result = json.loads(text)
            except Exception as e:
                error = f"Error analyzing image: {e}"

    return render_template_string(PAGE, result=result, error=error, notes=notes)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)