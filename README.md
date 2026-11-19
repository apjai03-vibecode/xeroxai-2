# 🖨️ XeroxAI — Local-First Print Shop & Cyber-Café Suite

> **Hacktoberfest Week 2 "Side Hustle" Challenge Entry**  
> Eliminating per-document token costs and privacy risks for independent print, stationery, and cyber-café operators using open-weight AI and on-premise execution.

---

## 💡 The Context & Side Hustle Challenge

Independent print shops and cyber-cafés operate on razor-thin margins while handling sensitive customer documents daily: government exam applications (UPSC, TNPSC, SSC), passport photos, national identity cards, legal affidavits, and curriculum vitae.

- **The Privacy Problem**: Cloud APIs (like OpenAI or closed vision APIs) expose confidential customer data to third-party data centers, creating regulatory and trust liabilities.
- **The Margin Problem**: Commercial per-document API charges destroy profitability for ₹2-₹10 printing jobs.
- **The Counter Workflow Bottleneck**: Counter operators juggle multiple manual tools: image editors to compress photos under government portal 50KB limits, word processors to format rough WhatsApp notes into biodata, and guesswork on turnaround times during peak rush hours.

**XeroxAI** is an offline-capable, local-first counter cockpit that runs entirely on local models and tools. It delivers instant, zero-cost, private processing at high counter speed.

---

## 🏆 Target Sponsor Alignment

| Sponsor | Integration Role | Implementation Details |
|---|---|---|
| **Google Gemma** | Local Open-Weight Document Field Extraction | `gemma2:2b` served via local Ollama (`http://localhost:11434/api/generate`) with structured JSON extraction of unstructured customer notes into standardized biodata fields. Includes deterministic heuristic fallback. |
| **Prior Labs (TabPFN-3.5)** | Foundation Tabular Queuing & Dynamic Pricing | `TabPFNRegressor` trained on cyber-café queue logs, predicting exact turnaround minutes from page counts, color modes, lamination requirements, and queue depth, with fair dynamic pricing calculations. |
| **Sentry** | Full-Pipeline Agent Tracing & Observability | Custom distributed spans (`llm.extraction`, `ml.tabpfn_prediction`, `image.processing`) via `sentry-sdk` capturing latency, token/char lengths, model metadata, and error handling. |
| **Render** | Multi-Service Production Hosting | Multi-service Infrastructure-as-Code blueprint (`render.yaml`) configuring unified deployment for the FastAPI Python backend and Next.js frontend. |

---

## ⚡ Core Functional Engines

### 1. Photo Spec Engine (`/api/resize-photo/`)
- **TNPSC / UPSC Govt Exams**: Strict `200x230 px` JPEG. Dynamic stepped compression and compliant padding guaranteeing final file size is **strictly between 20 KB and 50 KB**.
- **Standard Passport**: `35x45 mm` aspect ratio (`413x531 px` at 300 DPI equivalent) with automatic contrast enhancement for counter photo printing.
- **Official Signature**: Strict `140x60 px`, strictly under **20 KB**.

### 2. Biodata & Form Extraction Engine (`/api/generate-biodata/`)
- Accepts raw, scrawled customer notes or WhatsApp text pastes.
- Prompts local `gemma2:2b` via Ollama for structured JSON entity extraction (`full_name`, `dob`, `qualification`, `contact`, `email`, `address`, `skills`, `languages`).
- Generates a ready-to-print, single-page A4 PDF using **ReportLab** with 0.5-inch margins, modern sans-serif typography, and candidate declaration block.

### 3. Queue Turnaround & Dynamic Pricing Engine (`/api/estimate-job/`)
- Powered by **Prior Labs TabPFN-3.5** tabular foundation model.
- Features: `[page_count, is_color, needs_lamination, current_queue_customers]`.
- Recommends fair counter pricing: base sheet rates (₹2 B&W / ₹10 Color) + lamination fee (₹20) + dynamic rush queue buffer.

### 4. Sentry Agent Tracing & Observability
- Integrated Sentry SDK performance monitoring with custom spans.
- Live telemetry monitor exposing span duration and engine health to the counter dashboard.

---

## 🚀 Quickstart & Local Launch

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- [Ollama](https://ollama.ai) (optional, for live Gemma inference)

### 1. Pull the Gemma Model (Optional for Live Ollama)
```bash
ollama pull gemma2:2b
ollama run gemma2:2b
```
*(If Ollama is not installed or offline, XeroxAI automatically activates its deterministic heuristic fallback without crashing).*

### 2. Start the Backend API
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API Documentation will be live at `http://localhost:8000/docs`.

### 3. Run Automated Tests
```bash
cd backend
pytest -v
```

### 4. Start the Next.js Dashboard
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🛠️ Architecture & Directory Layout

```
xeroxai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, routes & Sentry init
│   │   ├── config.py            # App settings (Ollama URL, Sentry DSN, defaults)
│   │   ├── models.py            # Pydantic schemas (Biodata, Photo, Queue)
│   │   ├── photo_engine.py      # PIL resizing & binary-search 20-50KB compression
│   │   ├── biodata_engine.py    # Gemma Ollama caller & ReportLab A4 PDF generator
│   │   ├── estimator.py         # Prior Labs TabPFN regressor & pricing logic
│   │   └── telemetry.py         # Sentry span helpers & live metrics buffer
│   ├── tests/
│   │   ├── test_api.py          # FastAPI endpoint integration tests
│   │   ├── test_photo_engine.py # Strict 20-50KB and dimension checks
│   │   ├── test_biodata_engine.py # Schema & PDF generation checks
│   │   └── test_estimator.py    # TabPFN turnaround & pricing tests
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/                    # Next.js App Router Counter Dashboard
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # High-contrast counter dashboard
│   │   │   └── globals.css
│   │   ├── components/          # Counter cards & live monitors
│   │   └── lib/                 # API client & types
│   ├── package.json
│   └── tailwind.config.ts
├── render.yaml                  # Multi-service Render deployment spec
└── README.md
```

---

## 🌐 Deploy to Render

This repository includes a multi-service `render.yaml` blueprint. To deploy:
1. Push this repository to GitHub.
2. In the Render Dashboard, click **New +** -> **Blueprint**.
3. Select this repository; Render will automatically detect `render.yaml` and provision:
   - `xeroxai-backend`: FastAPI Python Web Service
   - `xeroxai-dashboard`: Next.js Static/Node Web Service
