# Supplier CoA Intelligence Engine — Scope & Design Reference

## Product
**Supplier CoA Intelligence Engine** by Wolvio Intelligence  
Demo target: India Pharma Expo 2026 (23–25 April, Hyderabad)

## Architecture

5-layer extraction pipeline:

```
INTAKE → EXTRACT → VALIDATE → STORE → INTERFACE
```

1. **INTAKE** — Accept PDF/JPG/PNG, render every page to PNG at 200 DPI
2. **EXTRACT** — Claude Vision with structured JSON prompt, Gemini 1.5 Flash fallback (confidence < 0.6)
3. **VALIDATE** — Parse spec limits, compare results, assign PASS/FAIL/WARNING/REVIEW/ERROR
4. **STORE** — PostgreSQL via Supabase (6 tables, full audit trail + JSONB raw extraction)
5. **INTERFACE** — Next.js 14 + Tailwind

## Database Schema (6 tables)

### Reference data
- `products` — product catalogue
- `spec_tables` — spec document versions per product
- `spec_parameters` — individual spec limits

### Transactional data
- `coa_submissions` — one row per uploaded CoA
- `coa_extractions` — AI extraction result (header + raw JSON)
- `coa_parameter_results` — validated result per parameter

## Spec Types

| Type | Examples |
|------|---------|
| MIN_ONLY | `NLT 98.0%`, `≥ 98.0`, `Not less than 98.0%` |
| MAX_ONLY | `NMT 0.5%`, `≤ 0.5%`, `<0.1%` |
| RANGE | `98.0 - 102.0%`, `2.0 to 3.0`, `98.0–102.0` |
| QUALITATIVE | `White crystalline powder` |
| PASSES | `Passes test`, `Conforms`, `Complies` |

## Validation Outcomes

| Status | Condition |
|--------|-----------|
| PASS | Within spec, >5% from boundary |
| WARNING | Within spec, ≤5% from boundary |
| FAIL | Outside spec |
| REVIEW | Qualitative / no spec / non-numeric result |
| ERROR | Extraction confidence < 0.6 |

## Demo Products

1. Paracetamol IP — 14 parameters (IP 2022)
2. Microcrystalline Cellulose PH102 — 13 parameters (NF 2023)
3. Gelatin Pharma Grade — 17 parameters (BP 2023)
