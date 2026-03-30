# Data Cleaning Toolkit

Clean messy tabular datasets (CSV, Excel, Parquet, JSON/JSONL) for analysis, dashboards, or machine learning.  
**Service:** Data Cleaning & Preparation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Problem

- Tabular files are often messy: missing values, duplicates, inconsistent date/number formats, mixed-case categories.
- Data is not ready for analysis or reporting.

This app **detects** common issues and **cleans** the data with configurable rules, then exports a cleaned file (CSV, Parquet, or JSON) and an HTML report.

---

## Flow

1. **Upload** one or more CSV, Excel, Parquet, or JSON files (or use built-in demo data). Multiple files are merged into one dataset.
2. **Detect** issues: missing values, duplicates, invalid formats, inconsistent categories, potential outliers (optional: duplicate key columns; columns as date/numeric; or run "Detect only" to preview without cleaning).
3. **Review** a compact **per-column insight** table (from detection, before cleaning), the issue summary, and cleaning options; then run clean when ready.
4. **See** a **before/after sample**, a short **cleaning summary**, and optional **same-index** row samples where cells changed. **Download** cleaned data (CSV, Parquet, or JSON) and the HTML report.

---

## How to run

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### Start the app

From the project root:

```bash
python -m streamlit run src/app.py
```

(If `streamlit` is on your PATH you can use `streamlit run src/app.py` instead.) The app opens in your browser; if it asks for an email on first run, you can leave it blank and press Enter.

### Run tests

```bash
python -m pytest
```

For quiet mode: `python -m pytest -q`.

### Optional: run the pipeline in a notebook

From project root, open and run:

- **`notebooks/01_pipeline_demo.ipynb`** — full pipeline (load → detect → clean → report) on the Sales demo.
- **`notebooks/02_prepare_demo_data.ipynb`** — generate `sales_messy.csv` and `customer_messy.csv` from clean templates (mixed dates, missing values, duplicates, inconsistent categories).

---

## Demo datasets

Two demos are included (with intentional issues):

| Demo       | Path                              | Typical issues                          |
|-----------|------------------------------------|-----------------------------------------|
| Sales     | `data/demo_sales/sales_messy.csv`  | Wrong date format, missing amount, duplicates, inconsistent region |
| Customer  | `data/demo_customer/customer_messy.csv` | Duplicates, inconsistent segment, missing values |

In the app, choose **Sales (messy)** or **Customer (messy)** to try the pipeline.

---

## Limitations

- **Recommended max ~100K rows** per file; very large files (>500K rows) may be slow or run out of memory. The app shows a warning above 100K rows and rejects uploads above ~25 MB (demo safeguard).
- **Batch only** — no real-time streaming.
- **Formats:** CSV, Excel (.xlsx), Parquet (.parquet), JSON (.json, .jsonl). Export as CSV, Parquet, or JSON.
- **Domain:** General tabular data. JSON/JSONL is supported with **one level** of nested-object flattening; deeply nested or highly custom structures are not the focus.

---

## License

MIT — see [LICENSE](LICENSE).
