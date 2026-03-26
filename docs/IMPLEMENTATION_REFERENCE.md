# Implementation Reference — Data Cleaning Toolkit

Repo structure, paths, demo data, and commands for development and deployment.

---

## 1. Repo structure

```
data-cleaning-toolkit/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── Dockerfile
├── docker-compose.yml
│
├── data/
│   ├── README.md                    # Demo data description and schema
│   ├── demo_sales/
│   │   └── sales_messy.csv          # Intentionally messy
│   └── demo_customer/
│       └── customer_messy.csv
│
├── src/
│   ├── __init__.py
│   ├── load.py                     # CSV, Excel, Parquet, JSON
│   ├── detect.py                   # Schema, issues, outliers
│   ├── clean.py                    # Cleaning rules (optional steps)
│   ├── schema.py                   # compare_schemas (before/after)
│   ├── report.py                   # Report generation (HTML + outliers + schema)
│   └── app.py                      # Streamlit entry (multi-file, export format)
│
├── notebooks/
│   ├── 01_pipeline_demo.ipynb      # Pipeline walkthrough (load → detect → clean → report)
│   └── 02_prepare_demo_data.ipynb  # Generate sales_messy.csv & customer_messy.csv from clean data
│
├── docs/
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── SERVICE_DESIGN.md
│   ├── IMPLEMENTATION_REFERENCE.md
│   ├── PROJECT_DECISION_RECORD.md
│   ├── IMPROVEMENTS_AND_RISKS.md
│   ├── V2_ROADMAP.md
│   └── DEPLOYMENT_ROADMAP.md
│
└── tests/
    ├── test_load.py
    └── test_detect_and_clean.py
```

---

## 2. requirements.txt

```
pandas
streamlit
openpyxl              # Excel
pyarrow               # Parquet
pytest
```

---

## 3. Paths and load

Example usage of the real API:

```python
from pathlib import Path
from src.load import load_table, load_demo_sales, load_demo_customer

# Demo helpers (used in tests and notebooks)
df_sales = load_demo_sales()          # loads data/demo_sales/sales_messy.csv
df_customer = load_demo_customer()    # loads data/demo_customer/customer_messy.csv

# Generic loader
path = Path("data/demo_sales/sales_messy.csv")
df = load_table(path)

# Optional: notebooks or save_html_report() can write reports to artifacts/reports/ (gitignored).
```

- **Load:** `load_table(path)` supports .csv, .xls/.xlsx, .parquet, .json, .jsonl. CSV encoding fallback: utf-8, cp1252, latin1.
- **App:** Multi-file upload (concat with `_source_file`); optional "Duplicate key columns" and "Columns as date/numeric"; run mode "Detect only" or "Detect and clean"; per-column **insight table** (pre-clean detection); cleaning-step checkboxes; **before/after head preview** and **same-index changed-row sample** (where applicable); bullet **cleaning summary** from `CleaningAction`s; export CSV, Parquet, or JSON; warning when rows > 100K; upload size guard; session state caches loaded data.
- **Outliers:** IQR-based outlier counts in issue summary and in HTML report (no auto-fix).
- **Schema:** `compare_schemas(df_a, df_b)` in `src/schema.py`; report includes "Schema comparison (Before vs After)".

---

## 4. Issue Detection Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| missing_threshold | 0.5 | Warn if column is 50%+ missing |
| duplicate_action | drop | Drop duplicate rows |
| date_formats | ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"] | Formats to try |

---

## 5. Demo Dataset Requirements (Concrete)

### Demo 1 — Sales

| Attribute | Value |
|-----------|-------|
| Source | Kaggle: [retail-sales-dataset](https://www.kaggle.com/datasets/manjeetsingh/retaildataset) or synthetic |
| File | `data/demo_sales/sales_messy.csv` |
| ~Rows | 500–2000 |
| Columns | order_id, order_date, product_id, amount, quantity, region, customer_id |
| Intentional issues | `order_date` mixed format (01/15/2024, 2024-01-15, 15-Jan-24), `amount` empty, `order_id` duplicates, `region` inconsistent (North/NORTH/north) |

### Demo 2 — Customer

| Attribute | Value |
|-----------|-------|
| Source | Kaggle: [telco-customer-churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) or synthetic |
| File | `data/demo_customer/customer_messy.csv` |
| ~Rows | 500–1000 |
| Columns | customer_id, signup_date, segment, lifetime_value, tenure |
| Intentional issues | `segment` inconsistent (Gold/gold/GOLD/Premium), `lifetime_value` NaN, duplicate `customer_id`, `signup_date` wrong format |

### Demo Data Preparation Steps

1. Download dataset from Kaggle (account required; manual download)
2. Save as `data/demo_sales/sales_messy.csv` and `data/demo_customer/customer_messy.csv`
3. **Add intentional issues** (Excel or Python):
   - `order_date`: Mixed format (01/15/2024, 2024-01-15, 15-Jan-24)
   - `amount`: Empty in some rows
   - `order_id`: Some duplicates
   - `region`: Inconsistent e.g. North, NORTH, north
   - `segment`: Gold, gold, GOLD, Premium
   - `lifetime_value`: NaN
4. Optional: run `notebooks/02_prepare_demo_data.ipynb` to generate the messy CSVs from clean templates

---

## 6. Commands

| Action | Command |
|--------|---------|
| Start app | `python -m streamlit run src/app.py` |
| Tests | `python -m pytest` |

---

## 7. .gitignore

```
__pycache__/
*.pyc
.venv/
venv/
.ipynb_checkpoints/
.pytest_cache/
.DS_Store
artifacts/reports/*
```

---

## 8. README & portfolio checklist

- [ ] **Repo name:** data-cleaning-toolkit
- [ ] **Description:** "Clean messy CSV/Excel datasets for analysis, dashboards, or ML"
- [ ] **README:** Problem, input → output flow, before/after example, how to run
- [ ] **Demo:** Screenshot or live link
- [ ] **Deliverables list:** What the client receives

---

