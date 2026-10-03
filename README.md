<div align="center">

# 🛡️ WarrantyCheck AI

**Intelligent Warranty Support Powered by Microsoft Foundry & GPT-5-mini**

[![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Microsoft Foundry](https://img.shields.io/badge/Microsoft_Foundry-AI-0078D4?style=flat-square&logo=microsoft&logoColor=white)](https://azure.microsoft.com/)
[![Azure Identity](https://img.shields.io/badge/Azure-DefaultAzureCredential-0078D4?style=flat-square&logo=microsoftazure&logoColor=white)](https://docs.microsoft.com/azure/developer/python/azure-sdk-authenticate)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

*Check warranty status · Analyze invoices with AI · Get instant claim guidance*

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### ⏱️ Warranty Calculator
- Deterministic calculation — **no AI guesswork**
- Returns exact expiry date, days remaining, and status
- Supports 1–5 year durations
- Validates against today's calendar date

</td>
<td width="50%">

### 📄 Document Analysis & Autofill
- Upload **PDF, DOCX, JPG, JPEG, PNG** (up to 10 MB)
- AI extracts: Product, Brand, Model, Serial, Date, Warranty Duration, Invoice No.
- One-click **"Use Extracted Information"** autofills the warranty form

</td>
</tr>
<tr>
<td width="50%">

### 💬 AI Warranty Assistant
- Real-time chat with the Microsoft Foundry `WarrantyCheckAI` agent
- Guides through claim procedures, required documents, and troubleshooting
- Quick prompt pills for common questions

</td>
<td width="50%">

### 🎨 Modern Light UI
- Clean, responsive design with tabbed navigation
- Animated loading indicators and status badges
- Drag & drop file upload zone
- Safe JSON error handling — no HTML crash errors

</td>
</tr>
</table>

---

## 📂 Project Structure

```
WarrantyCheckAI/
│
├── app.py                    # Flask entry point & JSON error handlers
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template (no secrets)
├── .gitignore                # Excludes .env, uploads/, __pycache__/
│
├── config/
│   └── config.py             # Loads & validates environment variables
│
├── routes/
│   ├── chat_routes.py        # POST /api/chat
│   ├── warranty_routes.py    # POST /api/check-warranty
│   └── document_routes.py    # POST /api/upload-document
│
├── services/
│   ├── foundry_service.py    # Microsoft Foundry agent integration
│   ├── warranty_service.py   # Deterministic warranty calculations
│   └── document_service.py   # PDF & DOCX text extraction
│
├── templates/
│   └── index.html            # Main UI template
│
├── static/
│   ├── css/style.css         # Modern light theme stylesheet
│   └── js/app.js             # Frontend controller & safe API client
│
└── uploads/                  # Uploaded documents (git-ignored)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Azure CLI (`az login`) — authentication uses `DefaultAzureCredential`
- Access to Microsoft Foundry with `WarrantyCheckAI` agent deployed

### 1. Clone the repository

```bash
git clone https://github.com/Sridhar84533/WarrantyCheckAI.git
cd WarrantyCheckAI
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Authenticate with Azure

```bash
az login
```

### 4. Create your `.env` file

Copy `.env.example` and fill in your values:

```bash
copy .env.example .env
```

```ini
FOUNDRY_PROJECT_ENDPOINT=https://warrantycheckai-resource.services.ai.azure.com/api/projects/WarrantyCheckAI
FOUNDRY_AGENT_NAME=WarrantyCheckAI
FOUNDRY_AGENT_VERSION=1
FLASK_SECRET_KEY=your-random-secret-key
MAX_UPLOAD_SIZE=10485760
UPLOAD_FOLDER=uploads
```

> **No API keys needed** — authentication is handled entirely by `DefaultAzureCredential` via `az login`.

### 5. Run the application

```bash
python app.py
```

Then open your browser:

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:5000` | Main Application |
| `http://127.0.0.1:5000/health` | Health Check (returns JSON) |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the web UI |
| `GET` | `/health` | Returns `{"status": "ok"}` |
| `POST` | `/api/check-warranty` | Calculate warranty status |
| `POST` | `/api/chat` | Chat with WarrantyCheckAI agent |
| `POST` | `/api/upload-document` | Upload & analyze document |

All API errors return clean JSON — never HTML.

---

## 🐍 Dependencies

```
Flask
python-dotenv
azure-ai-projects
azure-identity
pypdf
python-docx
python-dateutil
```

---

## 🔒 Security

- `.env` and `uploads/` are **excluded from version control** via `.gitignore`
- No API keys are stored in source code — uses Azure `DefaultAzureCredential`
- All API endpoints return structured JSON errors, never raw stack traces

---

## 👤 Author

**Sridhar84533**  
[GitHub](https://github.com/Sridhar84533) · [Sridhar040407@gmail.com](mailto:Sridhar040407@gmail.com)

---

<div align="center">

Made with  using Microsoft Foundry, Flask & Python

</div>