# Supplier CoA Intelligence Engine

AI-powered Certificate of Analysis extraction, validation, and audit trail for pharmaceutical QC.

**By Wolvio Intelligence** — India Pharma Expo 2026, Hyderabad

---

## What it does

Upload a supplier CoA (PDF or image) and within seconds receive:

- **Header extraction** — product, batch, supplier, dates with confidence scores
- **Parameter table** — every test parameter extracted into structured rows
- **Spec validation** — each parameter validated against internal specs
- **Colour-coded results** — PASS (green), WARNING (amber), FAIL (red), REVIEW (cyan), ERROR (orange)
- **CSV/JSON export** — full audit trail with confidence scores and boundary margins

---

## Architecture

```
PDF/Image
    ↓
INTAKE (PyMuPDF → PNG at 200 DPI)
    ↓
EXTRACT (Claude Vision → Gemini fallback if confidence < 0.6)
    ↓
VALIDATE (spec parser → comparator → 5% warning band)
    ↓
STORE (Supabase PostgreSQL — 6 tables + JSONB audit trail)
    ↓
INTERFACE (Next.js 14 + Tailwind)
```

---

## Project structure

```
coa-intelligence-engine/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # pydantic-settings
│   │   ├── api/routes/             # coa.py + specs.py endpoints
│   │   ├── core/
│   │   │   ├── extraction/         # intake, vision, prompts, merger, pipeline
│   │   │   ├── validation/         # spec_parser, comparator, matcher, engine
│   │   │   └── export/             # CSV + JSON exporter
│   │   ├── db/                     # Supabase client, models, queries
│   │   └── storage/                # File upload/download
│   ├── tests/                      # pytest test suite
│   ├── scripts/
│   │   ├── create_tables.sql       # Run in Supabase SQL editor
│   │   └── seed_specs.py           # Seed 3 demo products
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                    # Next.js App Router
│       ├── components/             # upload, results, sidebar, export
│       ├── hooks/                  # useCoaUpload, useCoaStatus, useCoaResult
│       └── lib/                    # API client + TypeScript types
└── docs/
    └── scope-design.md
```

---

## Setup

### 1. Supabase database

1. Create a Supabase project at supabase.com
2. Run `backend/scripts/create_tables.sql` in the SQL editor
3. Create a storage bucket named `coa-uploads` (private)

### 2. Backend

```bash
cd backend
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Seed demo products

```bash
cd backend
python scripts/seed_specs.py
```

### 4. Frontend

```bash
cd frontend
cp .env.example .env.local
# Set: NEXT_PUBLIC_API_URL=http://localhost:8000

npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Running tests

```bash
cd backend
pytest -v
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/coa/upload` | Upload CoA file, trigger extraction |
| GET | `/api/coa/status/{id}` | Poll extraction progress |
| GET | `/api/coa/result/{id}` | Full structured result |
| GET | `/api/coa/export/{id}?format=csv\|json` | Download audit export |
| GET | `/api/coa/submissions` | Recent submission list |
| POST | `/api/specs/parameters` | Seed spec library |

---

## Demo products

| Product | Pharmacopoeia | Parameters |
|---------|---------------|------------|
| Paracetamol IP | IP 2022 | 14 |
| Microcrystalline Cellulose PH102 | NF 2023 | 13 |
| Gelatin Pharma Grade | BP 2023 | 17 |

---

## Brand

- Navy `#1A2332` · Blue `#2563EB` · Slate `#475569` · Light Gray `#F1F5F9`
- PASS: green · WARNING: amber · FAIL: red · REVIEW: cyan · ERROR: orange
