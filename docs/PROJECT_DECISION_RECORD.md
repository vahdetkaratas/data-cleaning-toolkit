# Project decision record — Data Cleaning Toolkit

Scope, audience, and what ships. Implementation detail: [IMPLEMENTATION_REFERENCE.md](IMPLEMENTATION_REFERENCE.md), history: [CHANGELOG.md](CHANGELOG.md).

---

## Product

**Data Cleaning Toolkit** — clean client tabular data (CSV, Excel, Parquet, JSON/JSONL), surface quality issues, export cleaned files plus an HTML report. **Positioning:** data cleaning & preparation service.

**Pitch:** Fix messy tables—missing values, duplicates, bad dates/numbers—so the data is ready for analysis.

---

## Why this exists

- **Clear output:** Cleaned file (CSV / Parquet / JSON) + HTML report (issues, schema comparison, actions).
- **Audience:** SMBs, e-commerce, marketing, analysts.
- **Stack:** Python, pandas, Streamlit; load → detect → clean → report.

---

## Out of scope

| Area | Not building |
|------|----------------|
| Platform | Full data engineering / heavy ETL |
| Scale | Real-time streaming, Spark-scale “big data” |
| UI | Custom SPA (Streamlit is the UI) |

---

## Deliverables (what users get)

- Cleaned dataset (format of their choice).
- In-app **issue summary**, **column insights** (pre-clean detection), **before/after previews**, **cleaning summary** bullets.
- HTML report: overview, issue tables, **schema comparison (before vs after)**, outlier flags (IQR, not auto-fixed), cleaning actions.

---

## Technical choices

| Layer | Choice |
|-------|--------|
| Runtime | Python, pandas |
| UI | Streamlit |
| Excel | openpyxl |
| Report | HTML |

---

## Demo data

Two small demos in `data/demo_sales/` and `data/demo_customer/` with intentional issues. Regenerate from `notebooks/02_prepare_demo_data.ipynb` if needed.

---

## Deploy

**VPS + Docker + docker-compose**; HTTPS in front via **Caddy** ([DEPLOYMENT_ROADMAP.md](DEPLOYMENT_ROADMAP.md)) — Nginx documented there as optional. Streamlit Cloud remains an alternative hosting option.

---

## Limitations (state clearly)

- **Size:** Best around **10K–100K rows** per use; very large files may be slow or OOM. App warns above ~100K rows; uploads capped (~25 MB default guard).
- **Batch only** — not a streaming pipeline.
- **Formats:** CSV, `.xlsx`, Parquet, JSON / JSONL (one level of nested flattening for objects); not for deeply nested documents.
- **Risks:** Scope creep (“build a platform”) and rule explosion—keep detection rules focused.

---

## Presentation (already in the app)

Issue summary, column insights, before/after samples, same-index change sample where applicable, exports (data + HTML)—see README **Flow** and run the Streamlit app.
