# Project Decision Record — Data Cleaning Toolkit

Project scope, goals, and deliverables.

---

## 1. Selected Project

**Data Cleaning Toolkit**

A delivery-focused tool that cleans client data (CSV/Excel/Parquet/JSON), produces a quality summary, and delivers clear outputs. **Service:** Data Cleaning & Preparation.

**One-line pitch:** "I fix the data — clean missing values, duplicates, and format issues so it's ready for analysis." (EDA = summarize, AI Analysis = interpret)

---

## 2. Why This Project

- **Clear deliverable:** Cleaned data (CSV/Parquet/JSON) + report — user sees what was fixed.
- **Audience:** Small business, e-commerce, marketing teams, analysts.
- **Technical scope:** Pandas, validation, pipeline — load, detect, clean, report.

---

## 3. Rejected / Out of Scope

| Category | Rejected |
|----------|----------|
| Scope | Full data engineering platform, ETL pipeline |
| Feature | Real-time streaming, big data (Spark) |
| UI | Custom frontend (Next.js) — Streamlit is enough |
| Data | Not only CSV; Excel too; Excel optional |

---

## 4. Target Clients

- Small businesses
- Companies that want data analysis done
- E-commerce stores
- Marketing teams

---

## 5. Client Problem

The client comes with one or more of:
- CSV/Excel is messy
- Missing values, duplicate rows
- Date/number formats broken
- Data not ready for analysis

---

## 6. Deliverables (What the Client Gets)

- Cleaned dataset (CSV, Parquet, or JSON — user choice)
- Data quality summary (missing, duplicates, invalid formats, inconsistent categories, outliers)
- Schema comparison (before vs after) and cleaning actions in report
- HTML cleaning report (overview, issue tables, schema comparison, actions)

---

## 7. MVP Scope

- CSV upload
- Column type detection
- Missing value summary
- Duplicate row detection
- Invalid format detection
- Simple cleaning suggestions
- Cleaned file export
- Cleaning summary report

---

## 8. V2 Scope (implemented in 2.0.0)

- User-selected cleaning rules (checkboxes: drop duplicates, standardize categories, coerce numeric, parse dates)
- Outlier warning (IQR; in issue summary and HTML report)
- Schema comparison (before vs after in report; `compare_schemas`)
- Column standardization (already in clean; optional per-step in UI)
- Multi-file merge (upload multiple files → concat with `_source_file`)

See [V2_ROADMAP.md](V2_ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md) for details.

---

## 9. Technical Direction

| Component | Choice |
|-----------|--------|
| Language | Python |
| Data | pandas |
| UI | Streamlit |
| Excel | openpyxl (optional) |
| Report | HTML or markdown |

---

## 10. Demo Dataset

At least 2 demos: **Sales dataset**, **Customer dataset**. Intentionally flawed (missing, duplicates, inconsistent categories, wrong date formats).

**Source:** Kaggle retail/sales or customer dataset; add issues on top.

---

## 11. Open Questions

Historical notes; most scope decisions are closed (see CHANGELOG / V2_ROADMAP).

- Excel: supported (openpyxl).
- Report: HTML today; PDF optional future.
- Deploy path: **VPS + Docker + docker-compose**; HTTPS via **Caddy** (documented in `DEPLOYMENT_ROADMAP.md`; **Nginx** noted there as optional). Streamlit Cloud remains an optional alternative.

---

## 12. Risks

- **Scope creep:** Trying to build a "data engineering platform". Keep it small, clear, practical.
- **Over-engineering:** Too many detection rules — 5–6 core rules enough for MVP.

---

## 13. Limitations (State Clearly to Client)

- **Best for:** 10K–100K row CSV. Very large files (>500K rows) may be slow.
- **No real-time stream:** Batch only; live data streams not supported.
- **Format:** CSV, Excel (.xlsx), Parquet (.parquet), JSON (.json, .jsonl). Export as CSV, Parquet, or JSON. Multi-file upload supported (merged with source label).
- **Domain:** General tabular data. JSON/JSONL with **one level** of nested-object flattening is supported; deeply nested or highly custom structures are not the focus.

---

## 14. Client presentation checklist

Elements that present this project well to clients:

- [ ] **Before/after table** — Data sample before and after cleaning
- [ ] **Issue summary panel** — What issues were found, how many
- [ ] **Cleaned output preview** — Sample of cleaned data
- [ ] **1-minute flow** — Upload (single or multiple files) → Detect → Choose steps → Clean → Download (CSV/Parquet/JSON + HTML report)
- [ ] **Deliverables list** — Cleaned data (CSV, Parquet, or JSON) + HTML cleaning report (with schema comparison, outliers, actions)

