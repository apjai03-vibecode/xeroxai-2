
# 🖨️ XeroxAI 2.0 — Intelligent Print Shop & Document Automation System

**Eliminating per-document API costs, manual document cleanup, and billing errors for independent print, stationery, and digital service counters using local-first AI and computer vision.**

---

## 💡 The Problem & Solution
Independent print shops and digital service centers operate on tight margins while handling sensitive customer documents daily: government exam applications (UPSC, TNPSC, SSC), passport photos, identity documents, receipts, and biodata forms.

- **Privacy & Compliance:** Sending customer IDs, photos, and personal forms to external cloud APIs creates privacy liabilities. XeroxAI 2.0 runs document enhancement, entity extraction, and queue prediction locally.
- **Zero Per-Document Token Costs:** Cloud vision/LLM fees eat into ₹2–₹10 print jobs. Local execution keeps unit economics profitable.
- **Counter Workflow Automation:** Replaces juggling separate photo editors, manual skew/shadow cleanup, word processors, and calculator spreadsheets with a single unified counter workspace.

---

## ⚡ Core Functional Engines

### 1. SmartDoc AI (`/api/smartdoc/enhance`)
- **Universal Ingestion:** Accepts JPG, JPEG, PNG, WebP, and multi-page PDF documents.
- **Automated Geometry & Clarity Repair:** Laplacian blur detection, automatic deskewing, 4-point perspective distortion correction, and illumination/shadow normalization.
- **Zero-Hallucination Guarantee:** Uses deterministic pixel-level computer vision (OpenCV & Pillow)—never uses generative AI to rewrite or alter text, numbers, names, or personal details.

### 2. AI Order Assistant & Deterministic Smart Billing (`/api/orders/parse` & `/api/billing/calculate`)
- **Natural-Language Intake:** Operators enter counter requests like *"50 colour copies, double-sided, and 2 laminated sheets for Rahul"* to auto-populate itemized print jobs (with a built-in deterministic regex fallback when Ollama is offline).
- **100% Deterministic Rate Engine:** Computes totals strictly from shop-configured SQLite rates across B&W vs. Colour, Simplex vs. Duplex, A4/A3/Legal/Letter paper sizes, and lamination—AI never calculates or alters prices.

### 3. Order Management System (`/api/orders`)
- **Persistent SQLite Queue:** Generates sequential daily order IDs (`XRX-YYYYMMDD-XXXX`) with customer details, itemized JSON, and lifecycle tracking (`Pending` → `Processing` → `Completed`).
- **Live Counter Metrics:** Searchable and filterable order queue with real-time revenue and job status tallies.

### 4. Govt Photo Spec Engine (`/api/resize-photo/`)
- **TNPSC / UPSC Govt Exams:** Strict `200×230 px` JPEG with binary-search compression guaranteeing file size stays strictly between **20 KB and 50 KB**.
- **Standard Passport & Official Signature:** `35×45 mm` (`413×531 px`) contrast-enhanced portrait preset and `140×60 px` (< 20 KB) signature preset.

### 5. Biodata & Form Extraction Engine (`/api/generate-biodata/`)
- Converts rough customer notes or WhatsApp text into structured JSON fields using local `gemma2:2b` via Ollama (with heuristic fallback) and renders a ready-to-print single-page A4 PDF via ReportLab.

### 6. Queue Turnaround Estimator (`/api/estimate-job/`)
- Predicts turnaround wait times from page count, color mode, lamination, and live queue depth using Prior Labs TabPFN-3.5.

### 7. Pipeline Observability (`/api/telemetry`)
- Integrated Sentry SDK distributed tracing capturing execution latency across document cleanup, ML inference, and LLM extraction spans.

---

## 🚀 Quickstart & Local Launch

### Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **Ollama** *(optional, for live `gemma2:2b` inference; deterministic fallbacks activate automatically if offline)*

### 1. Start the FastAPI Backend
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Run Automated Test Suite (35 Passing Tests)

```bash
cd backend
pytest -v

```

### 3. Start the Next.js Counter Dashboard

```bash
cd frontend
npm install
npm run dev

```

Open `http://localhost:3000` in your browser.

---

## 🛠️ Architecture & Directory Layout

```text
xeroxai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, routes & Sentry init
│   │   ├── config.py            # Environment & runtime settings
│   │   ├── database.py          # SQLite persistence (orders & pricing_config)
│   │   ├── models.py            # Pydantic request/response schemas
│   │   ├── smartdoc_engine.py   # OpenCV/Pillow blur, deskew, warp & shadow cleanup
│   │   ├── order_engine.py      # Deterministic billing & NL order parser
│   │   ├── photo_engine.py      # Strict 20-50KB & dimension image resizer
│   │   ├── biodata_engine.py    # Gemma Ollama extractor & ReportLab A4 PDF builder
│   │   ├── estimator.py         # TabPFN queue turnaround predictor
│   │   └── telemetry.py         # Sentry span helpers & live metrics buffer
│   ├── tests/                   # 35 unit & integration tests (pytest)
│   └── requirements.txt
├── frontend/                    # Next.js App Router Counter Dashboard
│   ├── src/
│   │   ├── app/                 # Daylight dashboard layout & pages
│   │   ├── components/          # SmartDoc, Billing, Orders, Photo, Biodata & Queue UI
│   │   └── lib/                 # Typed API client & interfaces
│   └── package.json
└── README.md

```

```


```
