🛡 Phishix
Intelligent Scam, Phishing & Fraud Detection System

Phishix is an AI-powered security scanner that evaluates text, URLs and images to identify potential scams, phishing attempts and fraudulent intent.
The system features a FastAPI backend (Uvicorn) and an interactive modern dashboard frontend built with vanilla JS + CSS + HTML.

📌 Overview

Cybercrime is increasing rapidly — fraudulent messages, phishing websites and scam visuals are harder to distinguish every day.
Phishix provides real-time scam probability scoring to help users make safer decisions.

🔥 Key Features
Capability	Description
📝 Text Scam Scan	Detect suspicious patterns, urgency, claim-based fraud language
🔗 URL Risk Detection	Validates phishing domains, redirects, anomalies
🖼 Image/Screenshot Analysis	OCR + scam-intent scoring on visual elements
📊 Scam Probability Index	Confidence score returned 0–100%
🌓 Theme Adaptive UI	Light/Dark mode toggle
⚡ FastAPI Backend	Low-latency inference via Uvicorn
🔐 Secure Client-Server Design	No browser-side evaluation leakage

Future-Ready Extensions → ML integration, deep phishing model, browser extension.

🏗 Project Structure
scam_detect/
└── scamsniper/
    ├── app/                # Backend (FastAPI)
    │   ├── main.py         # Entry point
    │   ├── util/           # Helpers & pipelines
    │   ├── models/         # ML models (optional)
    │   └── requirements.txt
    │
    └── frontend/           # Web UI
        ├── index.html
        ├── style.css
        └── app.js

🚀 Getting Started
1️⃣ Backend Setup — FastAPI + Uvicorn
cd scam_detect/scamsniper/app
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000


API will start here:

🔗 http://localhost:8000
⚙ Swagger Docs → http://localhost:8000/docs

2️⃣ Frontend Setup
cd ../frontend
npx live-server          # or use VS Code Live Server


UI loads at:
🔗 http://127.0.0.1:5500/

Both frontend + backend must run simultaneously.

📡 API Endpoints
Method	Endpoint	Purpose
POST	/analyze/text	Scan text & return scam score
POST	/analyze/url	Evaluate URL risk level
POST	/analyze/image	OCR + phishing intent detection

Sample JSON response:

{
  "risk_score": 72,
  "verdict": "Likely Scam",
  "flags": ["Urgency", "Financial lure", "Grammar anomalies"]
}

🔐 Security Considerations
Risk	Mitigation
User leaks through logs	Tokenize user input before storage
URL fetch risk	Disable auto-execution/redirect following
OCR image injection	Validate MIME + sanitize before pipeline

Designed to be privacy-first — no external API dependency required.

📊 Roadmap

 Train real phishing intent transformer model

 Add user history, reports & threat insights

 Deploy cloud inference API

 Browser extension for real-time site scanning

 Mobile Lite version (Android + iOS)

🖥 UI Preview

(Insert screenshots here — I can generate mockups if you want)

📌 Dashboard Home     🔍 Text Scanner
🖼 Image Scan         🔗 URL Analyzer
📊 Result Metrics     🌓 Theme Switch

📝 License

MIT License — use freely with attribution.

Phishix
Maintained by: you
