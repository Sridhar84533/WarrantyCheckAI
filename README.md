# WarrantyCheck AI 🛡️

**WarrantyCheck AI** is an intelligent warranty support web application built with Python Flask and powered by Microsoft Foundry. It offers deterministic warranty calculations, intelligent invoice/receipt document analysis with automated form population, and a conversational AI Warranty Assistant.

---

## 🚀 Key Features

1. **Warranty Calculator**
   - Deterministic calculation of warranty status (*Within Warranty* vs *Warranty Expired*), exact expiry date, and days remaining.
   - Configurable warranty duration options (1 to 5 years).
   - Validates purchase date and product details against current calendar dates.

2. **AI Document Analysis & Form Autofill**
   - Upload invoices, purchase receipts, or warranty certificates in **PDF**, **DOCX**, **JPG**, **JPEG**, or **PNG** formats (up to 10 MB).
   - Extracts document text using `pypdf` and `python-docx` (including tables).
   - Microsoft Foundry Agent parses key parameters: *Product Name, Brand, Model Number, Serial Number, Purchase Date, Duration, and Invoice Number*.
   - One-click **"Use Extracted Information"** button to automatically populate and review the warranty check form.

3. **AI Warranty Assistant**
   - Real-time conversational interface connected to the Microsoft Foundry `WarrantyCheckAI` agent (`gpt-5-mini`).
   - Guides users through claim procedures, required documentation, exclusion clauses, and safe basic troubleshooting.

4. **Modern Light UI**
   - Clean, accessible light theme with responsive cards, status badges, animated loading states, and tabbed navigation.
   - Resilient frontend network error handling preventing JSON parse crashes.

---

## 📂 Project Structure

```text
Project/
├── app.py                      # Flask main application entry point & error handlers
├── .env.example                # Template configuration (no secrets)
├── .gitignore                  # Git ignore rules (.env, uploads, pycache)
├── requirements.txt            # Python dependencies
├── config/
│   └── config.py               # Application configuration & env loader
├── routes/
│   ├── chat_routes.py          # POST /api/chat route
│   ├── warranty_routes.py      # POST /api/check-warranty route
│   └── document_routes.py      # POST /api/upload-document route
├── services/
│   ├── foundry_service.py      # Microsoft Foundry agent integration
│   ├── warranty_service.py     # Deterministic warranty calculations
│   └── document_service.py     # Document text extraction (PDF & DOCX)
├── templates/
│   └── index.html              # Frontend user interface
├── static/
│   ├── css/
│   │   └── style.css           # Modern stylesheet
│   └── js/
│       └── app.js              # Frontend controller & safe API client
└── uploads/                    # Secure local storage for uploaded documents
```

---

## 🛠️ Prerequisites & Installation

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd Project
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Authenticate with Azure CLI
The application uses Azure's `DefaultAzureCredential` locally. Make sure you are logged in:
```bash
az login
```

### 4. Configure environment variables
Create a `.env` file in the root folder based on `.env.example`:
```ini
FOUNDRY_PROJECT_ENDPOINT=https://warrantycheckai-resource.services.ai.azure.com/api/projects/WarrantyCheckAI
FOUNDRY_AGENT_NAME=WarrantyCheckAI
FOUNDRY_AGENT_VERSION=1
FLASK_SECRET_KEY=your-random-secret-key
MAX_UPLOAD_SIZE=10485760
UPLOAD_FOLDER=uploads
```
*(No API keys needed in `.env` — Azure CLI handles the identity authentication).*

---

## 💻 Running the Application

Start the Flask server:
```bash
python app.py
```

Open your browser and navigate to:
- **Application:** `http://127.0.0.1:5000`
- **Health Check:** `http://127.0.0.1:5000/health`

---

## 🔒 Security
- All sensitive environment credentials (`.env`) and uploaded files (`uploads/`) are excluded from version control via `.gitignore`.
- API endpoints strictly return JSON error responses rather than exposing stack traces or HTML.
