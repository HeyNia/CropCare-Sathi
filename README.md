<div align="center">

# 🌱 CropCare Sathi

### Your smart companion for healthier crops

A multilingual AI-powered crop-health assistant that analyzes plant images, provides practical guidance, stores diagnosis history, and generates downloadable PDF reports.

<p>
  <a href="https://github.com/YOUR_GITHUB_USERNAME/cropcare-sathi">
    <img src="https://img.shields.io/badge/Project-CropCare%20Sathi-1b6b3a?style=for-the-badge&logo=leaf&logoColor=white" alt="CropCare Sathi">
  </a>
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

<p>
  <a href="#-features">Features</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-project-structure">Structure</a> •
  <a href="#-future-roadmap">Roadmap</a>
</p>

</div>

## 🌐 Live Demo

Try CropCare Sathi here:

[Open Live Prototype](https://cropcare-sathi.onrender.com)
---

## ✨ What is CropCare Sathi?

CropCare Sathi is a Flask-based AI crop-health assistant designed to help farmers and learners understand visible plant symptoms from a single image.

Users can upload a crop or plant image, select a diagnosis language, add field notes, and receive an AI-assisted crop-health assessment powered by Google Gemini.

The application also stores previous reports in SQLite, displays uploaded images, provides a dashboard, and generates downloadable PDF reports.

> **CropCare Sathi is an advisory tool, not a replacement for professional agricultural or laboratory diagnosis.**

---

## 🚀 Features

| Feature | Description |
|---|---|
| 📷 Image diagnosis | Upload PNG, JPG, JPEG, or WEBP crop images |
| 🤖 Gemini vision analysis | Analyze visible plant symptoms using Google Gemini |
| 🌐 Multilingual output | Request the diagnosis in a preferred language |
| 📝 Farmer notes | Add crop name, symptom duration, weather, watering, or pest details |
| 📊 Dashboard | View diagnosis totals and recent reports |
| 🗂️ History | Save, search, and reopen previous diagnosis reports |
| 🖼️ Image display | View the original uploaded image with each report |
| 📄 PDF download | Download a formatted crop diagnosis report |
| 📚 Knowledge base | Read practical crop-observation and photo-taking guidance |
| 🐳 Docker support | Run the complete application in a container |
| 🔐 Secret management | Keep API credentials outside the source code |

---

## 🧠 How It Works

```text
Upload crop image
        │
        ▼
Flask validates the image and farmer notes
        │
        ▼
Google Gemini analyzes the image
        │
        ▼
Diagnosis is saved in SQLite
        │
        ├──► Result page
        ├──► Dashboard
        ├──► Diagnosis history
        └──► Downloadable PDF report
```

---

## 🛠️ Technology Stack

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Google%20Gemini-8E75B2?style=flat-square&logo=google&logoColor=white" alt="Google Gemini">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white" alt="CSS3">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
</p>

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Flask | Web server, routes, forms, and templates |
| Google Gemini | Multimodal crop-image analysis |
| SQLite | Diagnosis history storage |
| ReportLab | PDF report generation |
| HTML, CSS, JavaScript | User interface |
| Docker | Containerized deployment |
| Waitress | Production WSGI server |

---

## 🖥️ Application Pages

| Route | Purpose |
|---|---|
| `/` | Upload an image and request a diagnosis |
| `/dashboard` | View diagnosis statistics and recent reports |
| `/history` | Search and browse saved diagnoses |
| `/history/<id>` | View one complete diagnosis report |
| `/knowledge` | Read crop-health guidance |
| `/download/<id>` | Download a diagnosis as PDF |

---

## 📸 Image Tips

For better image-based guidance:

- Take photos in natural daylight.
- Keep the affected area in focus.
- Avoid blurry, dark, or heavily filtered images.
- Photograph the affected leaf, fruit, stem, or plant clearly.
- If possible, capture both sides of an affected leaf.
- Add the crop name and symptom duration in the notes field.
- Include useful information about rainfall, watering, pests, or fertilizer use.

---

## ⚡ Quick Start

### Prerequisites

Install the following:

- Python 3.14 or later
- Git
- Docker Desktop — optional, for containerized execution
- A Gemini API key

### Clone the repository

```bash
git clone [https://github.com/YOUR_GITHUB_USERNAME/cropcare-sathi.git](https://github.com/YOUR_GITHUB_USERNAME/cropcare-sathi.git)
cd cropcare-sathi
```

### Create a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### Create the `.env` file

Create a file named `.env` beside `app.py`:

```env
GEMINI_API_KEY=your_real_gemini_api_key
FLASK_SECRET_KEY=your_long_random_flask_secret
```

Generate a random Flask secret:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

> Never commit `.env` to GitHub.

### Start the application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:8080/
```

---

## 🐳 Run with Docker

### Build the image

```powershell
docker build -t cropcare-sathi .
```

### Start the container

```powershell
docker run `
  --name cropcare-sathi-container `
  --env-file .env `
  -p 8080:8080 `
  -v "${PWD}\static\uploads:/app/static/uploads" `
  -v "${PWD}\agrin_history.db:/app/agrin_history.db" `
  cropcare-sathi
```

Open:

```text
http://localhost:8080/
```

The mounted folders preserve:

```text
static/uploads/
agrin_history.db
```

so uploaded images and diagnosis history remain available when the container is rebuilt or replaced.

### Stop the container

```powershell
docker stop cropcare-sathi-container
```

### Start it again

```powershell
docker start cropcare-sathi-container
```

### View logs

```powershell
docker logs -f cropcare-sathi-container
```

---

## 📂 Project Structure

```text
cropcare-sathi/
│
├── app.py
├── Dockerfile
├── requirements.txt
├── README.md
├── .gitignore
├── .dockerignore
│
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   ├── history.html
│   ├── history_detail.html
│   └── knowledge.html
│
└── static/
    ├── style.css
    ├── script.js
    └── uploads/
```

The following local files are intentionally excluded from GitHub:

```text
.env
agrin_history.db
static/uploads/
.venv/
.idea/
```

---

## 🔒 Security

Never upload these files to GitHub:

```text
.env
```

```text
agrin_history.db
```

```text
static/uploads/
```

The `.env` file contains:

- `GEMINI_API_KEY`
- `FLASK_SECRET_KEY`

If your Gemini API key is ever exposed:

1. Revoke the exposed key immediately.
2. Create a replacement key.
3. Update your local `.env`.
4. Remove the secret from Git history if it was committed.

---

## ⚠️ Disclaimer

CropCare Sathi provides AI-assisted, image-based crop-health guidance.

The result may be inaccurate because symptoms can have multiple causes, including:

- Disease
- Pest damage
- Nutrient deficiency
- Water stress
- Weather conditions
- Soil conditions
- Physical damage

For severe, rapidly spreading, or high-value crop problems, contact a local agriculture officer, plant-pathology expert, extension worker, or qualified crop consultant.

Always follow local regulations and product labels before using agricultural chemicals.

---

## 🗺️ Future Roadmap

- [ ] Add farmer login and user profiles
- [ ] Add PostgreSQL for production deployments
- [ ] Store images using Cloudinary, Supabase Storage, or Amazon S3
- [ ] Add crop-specific disease categories
- [ ] Add weather-based crop recommendations
- [ ] Add image comparison for symptom progression
- [ ] Add diagnosis confidence visualization
- [ ] Add farmer feedback for improving results
- [ ] Add deployment to Hugging Face Spaces
- [ ] Add a public demo link
- [ ] Add automated tests with Pytest

---

## 👨‍💻 Developer

Built by **Nisha Maurya**

Early-career software developer focused on:

```text
Python · Flask · .NET · PostgreSQL · React · JavaScript · Git · Docker · AI Integration
```

If you find this project useful, consider giving the repository a ⭐.

---

## 📄 License

This project is created for educational, portfolio, and hackathon purposes.
