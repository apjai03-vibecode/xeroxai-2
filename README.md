
# XeroxAI 2.0 — Smart Print Shop & Document Automation System

XeroxAI 2.0 is a local-first counter workspace built for independent print shops, stationery stores, and digital service centers. It automates document cleanup, government exam photo resizing, natural-language order entry, and billing calculations without sending customer files to third-party cloud APIs.

---

## Chosen Vertical
**Open Innovation** (Print & Digital Service Counter Automation)

---

## Approach and Logic
1. **Local-First Privacy:** Print shops handle sensitive customer records every day, including exam forms, ID cards, passport photos, and resumes. XeroxAI 2.0 processes documents, images, and order records directly on the host server rather than sending customer data to external commercial AI APIs.
2. **Strict Accuracy Guardrails:**
   - **No Altered Text:** SmartDoc AI uses computer vision (OpenCV and Pillow) instead of generative image models so names, numbers, dates, and signatures are never rewritten or distorted.
   - **Deterministic Billing:** Natural-language order parsing extracts job requirements (copies, color mode, double-sided, paper size, lamination), while final prices are calculated strictly from shop-configured database rates. AI never calculates or guesses prices.
3. **Offline and Cloud Resilience:** When a local Ollama (`gemma2:2b`) node is running on the shop computer, entity extraction uses local model inference. In hosted web deployments where local Ollama is unavailable, the backend automatically switches to a deterministic rule-based parser so every feature works reliably.

---

## How the Solution Works

### 1. SmartDoc AI (`/api/smartdoc/enhance`)
- Supports JPG, JPEG, PNG, WebP, and multi-page PDF uploads.
- Checks image sharpness, detects page tilt, straightens skewed borders, removes shadows, and enhances contrast while keeping the original file intact.

### 2. AI Order Assistant and Smart Billing (`/api/orders/parse` & `/api/billing/calculate`)
- Lets operators type or paste plain-English requests (for example: *"50 colour copies, double-sided, and 2 laminated sheets for Rahul"*) to auto-fill itemized print jobs.
- Calculates exact totals in Indian Rupees (INR) across Black & White vs. Colour, Single-sided vs. Double-sided, A4 / A3 / Legal / Letter paper sizes, and lamination using customizable shop rates stored in SQLite.

### 3. Order Management (`/api/orders`)
- Generates sequential daily order IDs (`XRX-YYYYMMDD-XXXX`) with customer details, itemized breakdowns, and live status tracking (`Pending`, `Processing`, `Completed`) with search and filtering.

### 4. Govt Photo Spec Engine (`/api/resize-photo/`)
- **TNPSC / UPSC Preset:** Resizes images to `200x230 px` JPEG and compresses them strictly between **20 KB and 50 KB**.
- **Passport and Signature Presets:** Formats `35x45 mm` (`413x531 px`) portraits and `140x60 px` (< 20 KB) signatures.

### 5. A4 Biodata Maker (`/api/generate-biodata/`)
- Extracts structured candidate details from rough customer notes or WhatsApp text and generates a ready-to-print single-page A4 PDF.

### 6. Queue Turnaround Estimator (`/api/estimate-job/`)
- Estimates customer wait times based on page count, color mode, lamination, and current counter queue depth.

---

## Assumptions Made
- **Currency and Rates:** All default printing and lamination prices are set in Indian Rupees (INR) and can be updated anytime by the shop operator.
- **Local vs. Cloud Execution:** In a local shop setup, Ollama (`gemma2:2b`) runs on `localhost:11434`. In hosted web demos without a local Ollama instance, deterministic parsing handles order and biodata extraction automatically.
- **Demo Database Persistence:** On free stateless cloud hosting, SQLite resets when the container restarts, whereas on a shop PC it persists permanently across reboots.

---

## Local Setup and Verification

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

### 2. Run Automated Tests (35 Passing Tests)

```bash
cd backend
pytest -v

```

### 3. Start the Next.js Frontend

```bash
cd frontend
npm install
npm run dev

```

Open `http://localhost:3000` in your browser.

```

```
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
