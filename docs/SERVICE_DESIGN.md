# Data Cleaning Toolkit — Service Design

Technical flow and module design.

---

## 1. Service Pipeline Overview

```
CSV / Excel / Parquet / JSON (single or multiple files)
        │
        ▼
┌───────────────────┐
│ Schema Detection  │  column types, dtypes
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Issue Detection   │  missing, duplicates, invalid format
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Cleaning Summary  │  issues found, suggestions
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Cleaning Actions  │  (user applies or auto-apply)
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Export            │  cleaned CSV / Parquet / JSON + HTML report
└───────────────────┘
```

**User flow:** Upload (one or more files) → Detect Issues → Review column insights + issue summary → Choose cleaning steps → Apply Cleaning → Review before/after samples + cleaning summary → Download Result (CSV/Parquet/JSON + HTML report)

---

## 2. Input / Output

| Stage | Format | Description |
|-------|--------|-------------|
| Input | CSV, Excel, Parquet, JSON (.json, .jsonl) | Client data; multiple files merged with `_source_file` |
| Issue report | HTML (and in-app summary) | Missing, duplicates, invalid formats, inconsistent categories, outliers |
| Output | CSV, Parquet, or JSON | Cleaned data (user choice) |
| Cleaning report | HTML | Summary with schema comparison (before vs after), outliers, cleaning actions |

---

## 3. Issue Taxonomy (Issues to Detect)

| Issue | Detection | Suggestion |
|-------|-----------|------------|
| Missing values | NaN, empty, placeholder | Impute or drop |
| Duplicates | row hash | Drop duplicates |
| Invalid format | date parse fail, numeric parse fail | Fix format |
| Inconsistent categories | "Yes"/"yes"/"Y" | Standardize |
| Wrong dtypes | string should be numeric | Convert |

---

## 4. Modules

| Module | Role |
|--------|------|
| load | Read CSV, Excel, Parquet, JSON (.json, .jsonl) |
| detect | Schema/column types, issues (missing, duplicates, invalid formats, inconsistent categories, outliers) |
| clean | Transformation rules (optional: drop duplicates, standardize categories, coerce numeric, parse dates) |
| schema | compare_schemas (before vs after) for report |
| report | HTML report (overview, missing, invalid formats, inconsistent categories, outliers, schema comparison, cleaning actions) |
| app | Streamlit: multi-file upload, options, column insights, before/after previews, cleaning summary, export CSV/Parquet/JSON |

---

## 5. Demo Scenarios

| Demo | Data | Intentional Issues |
|------|------|--------------------|
| Sales | date, product, amount, region | Wrong date format, missing amount, duplicate orders |
| Customer | id, signup_date, segment, value | Duplicates, inconsistent segment, missing value |

---

## 6. Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | Python, pandas |
| UI | Streamlit |
| Excel | openpyxl (optional) |
| Report | HTML report |

---

