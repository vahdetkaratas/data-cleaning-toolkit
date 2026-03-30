# Implementation reference — Data Cleaning Toolkit

Repo layout, API notes, commands, deployment assets.

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
├── data/
│   ├── README.md
│   ├── demo_sales/sales_messy.csv
│   └── demo_customer/customer_messy.csv
├── src/
│   ├── __init__.py
│   ├── load.py
│   ├── detect.py
│   ├── clean.py
│   ├── schema.py
│   ├── report.py
│   └── app.py
├── notebooks/
│   ├── 01_pipeline_demo.ipynb
│   └── 02_prepare_demo_data.ipynb
├── docs/
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── SERVICE_DESIGN.md
│   ├── IMPLEMENTATION_REFERENCE.md
│   ├── PROJECT_DECISION_RECORD.md
│   └── DEPLOYMENT_ROADMAP.md
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

## 3. API and app behavior

```python
from pathlib import Path
from src.load import load_table, load_demo_sales, load_demo_customer

df_sales = load_demo_sales()
df_customer = load_demo_customer()
df = load_table(Path("data/demo_sales/sales_messy.csv"))
```

- **Load:** `.csv`, `.xls`/`.xlsx`, `.parquet`, `.json`, `.jsonl`. CSV encoding tries utf-8, cp1252, latin1.
- **App:** Multi-file merge with `_source_file`; duplicate-key and date/numeric overrides; detect-only vs detect+clean; column insight table; before/after head preview; same-index changed-row sample when applicable; cleaning summary from `CleaningAction`s; export CSV / Parquet / JSON; ~25 MB upload guard; 100K row warning; `st.session_state` cache for loaded data.
- **Outliers:** IQR counts in summary and HTML only (no auto-removal).
- **Schema:** `compare_schemas()` in `src/schema.py` feeds the report.

### Testing note

**pytest** covers `load`, `detect`, `clean`, `report`, and integration paths. There is **no** automated end-to-end or Streamlit UI test (e.g. Playwright); that remains a manual check.

---

## 4. Detection parameters (reference)

| Parameter | Default | Meaning |
|-----------|---------|---------|
| missing_threshold | 0.5 | Flag if column is ≥50% missing |
| duplicate_action | drop | Duplicate rows dropped when cleaning |
| date_formats | several | Strings tried when parsing dates |

---

## 5. Demo data

Shipped CSVs are **small intentional samples** (a handful of rows) for fast demos. The notebook `02_prepare_demo_data.ipynb` can regenerate them from templates.

| Demo | File | Issues illustrated |
|------|------|---------------------|
| Sales | `data/demo_sales/sales_messy.csv` | Mixed dates, missing amount, duplicate key, region casing |
| Customer | `data/demo_customer/customer_messy.csv` | Duplicates, segment casing, missing value, date format |

For larger samples, extend `notebooks/02_prepare_demo_data.ipynb` or swap in your own CSVs with the same column patterns.

---

## 6. Commands

| Action | Command |
|--------|---------|
| App | `python -m streamlit run src/app.py` |
| Tests | `python -m pytest` |

---

## 7. .gitignore (summary)

Ignores virtualenvs, `__pycache__`, `.pytest_cache`, notebooks checkpoints, coverage, `.env` / secrets, `artifacts/reports/*`, editor junk. See repo root `.gitignore` for the full list.
