# Changelog

All notable changes to the Data Cleaning Toolkit are documented here.

---

## [2.1.1] — 2026-03-30

### Documentation

- Deployment guide (`DEPLOYMENT_ROADMAP.md`) is English-only; **Caddy** primary, **Nginx** optional.
- Removed redundant docs: `V2_ROADMAP.md` and `IMPROVEMENTS_AND_RISKS.md` (content folded into this file and `IMPLEMENTATION_REFERENCE.md`).
- Trimmed `PROJECT_DECISION_RECORD.md`; refreshed `docs/README.md` index.

---

## [2.1.0] — 2025-03

### Added

- **Missing values handling:** In cleaning, user can choose: leave as is (default), drop rows with any missing, or fill with a value. `basic_clean()` accepts `missing_action` ("drop" | "fill" | None) and `fill_missing_value` (default 0). App: "Missing values" radio and optional "Fill value" input.
- **Nested JSON flatten:** When loading `.json` or `.jsonl`, if objects contain nested dicts, one level is flattened via `pd.json_normalize()` (e.g. `meta.x`, `meta.y`). Flat JSON unchanged. New helper `_load_json_flatten()` in `load.py`.

### Tests

- `test_clean_missing_action_drop`, `test_clean_missing_action_fill`, `test_load_table_json_nested_flatten`.

---

## [2.0.0] — 2025-03 (V2)

### Added

- **Outliers in HTML report:** Summary includes `outliers`; HTML report has a "Potential outliers (IQR)" section (column, count, method).
- **Integration test:** Pipeline asserts `report_to_bytes` content (Overview, Potential outliers, Cleaning Actions, Schema comparison) and `summary["outliers"]`.
- **Parquet & JSON support:** `load_table()` and app upload accept `.parquet`, `.json`, `.jsonl`. Export format selector: CSV (default), Parquet, or JSON. Dependency: `pyarrow`.
- **User-selected cleaning rules:** Checkboxes in app: Drop duplicate rows, Standardize categories, Coerce numeric columns, Parse date columns. `basic_clean()` accepts `drop_duplicates`, `standardize_categories`, `coerce_numeric`, `parse_dates` (all default True).
- **Schema comparison:** New `src/schema.py` with `compare_schemas(df_a, df_b)`. Report includes "Schema comparison (Before vs After)" with dtype changes and column add/remove. Summary includes `schema_comparison`.
- **Multi-file merge:** File uploader accepts multiple files; when 2+ files are selected, they are concatenated with a `_source_file` column and processed as one dataset. Source label shows "Merged: N files — …".

### Changed

- `build_summary_table()` adds `outliers` and `schema_comparison` to the summary dict.
- `render_html_report()` renders outlier and schema-comparison sections.
- App: export as CSV/Parquet/JSON; cleaning step checkboxes; multi-file upload.

---

## [1.3.0] — 2025-03

### Added

- **Logging:** `load.py` logs file-not-found and CSV decode failures; `app.py` logs upload read failures (with exception details) for easier debugging in deployment.
- **Report download via stream:** HTML report is generated in memory (`report_to_bytes()`) and passed directly to the download button; no write to `artifacts/reports/` then read back.
- **Portfolio note:** README section "Portfolio / showcase" with a short note on adding before/after screenshots (issue summary + cleaned result).

### Changed

- App uses `report_to_bytes(summary)` for the "Download cleaning report (HTML)" button instead of `save_html_report` + file read. `save_html_report()` remains available for tests and optional file output.

---

## [1.2.0] — 2025-03

### Added

- **Session state:** Loaded dataframe and source are cached in `st.session_state`; changing options (e.g. threshold, run mode) no longer requires re-uploading or re-selecting demo.
- **Column type override:** Optional UI inputs "Columns to treat as date" and "Columns to treat as numeric" (comma-separated). Passed as `type_overrides` to `detect_issues()` and `basic_clean()`; overrides name-based inference (e.g. `created_at`, `revenue`).
- **Outlier detection:** Numeric columns are checked for potential outliers (IQR method). Issue summary shows per-column outlier counts; no auto-fix, report only.
- **Integration test:** `test_integration_pipeline_from_file` loads from `data/demo_sales/sales_messy.csv`, runs detect → clean → report, and asserts report content and summary row counts.

### Changed

- `infer_column_types()` and `detect_issues()` accept optional `type_overrides: Dict[str, str]`.
- `basic_clean()` accepts optional `type_overrides` and passes it to type inference.

---

## [1.1.0] — 2025-03

### Added

- **CSV encoding:** `load_table()` tries utf-8, cp1252, latin1 in order; optional `encoding=` argument. Upload uses same fallback in `_read_uploaded_file()`.
- **Large file warning:** App shows a warning when the dataset has more than 100K rows. README recommends max ~100K rows.
- **Duplicate key columns in UI:** Optional text input (comma-separated column names); passed to `detect_issues(key_columns=...)` and `basic_clean(duplicate_key_columns=...)`.
- **Run mode:** "Detect only" (show issues, no cleaning) or "Detect and clean" (full pipeline with download).
- **Upload error handling:** Empty file, encoding errors, empty Excel, and invalid data show short user-facing messages; CSV upload tries multiple encodings.

### Changed

- README Limitations: clarified recommended max size and that the app warns above 100K rows.

---

## [1.0.0] — 2025-03

### Added

- **Core pipeline:** Load CSV/Excel → detect issues → clean → export CSV + HTML report.
- **Issue detection:** Missing values, duplicates (configurable key columns), invalid date/numeric formats, inconsistent categories.
- **Cleaning:** Drop duplicates, standardize categories (with opt-in/opt-out columns), coerce numeric/date columns.
- **Streamlit app:** File upload, demo datasets (Sales, Customer), issue summary, cleaned data preview, download CSV and report.
- **Demo datasets:** Sales and Customer with intentional issues under `data/demo_sales/` and `data/demo_customer/`.
- **Tests:** Load, detect, clean, report (including edge cases and HTML escape).

### Security

- HTML report: all dynamic content escaped to prevent XSS.

### Changed

- Pandas: replaced deprecated `is_categorical_dtype` with `isinstance(..., pd.CategoricalDtype)`.
- Duplicate logic: parametrized via `key_columns` (detect) and `duplicate_key_columns` (clean).
- Category standardization: optional `standardize_only_columns` and `skip_standardize_columns` in `basic_clean`.

### Documentation

- README: problem, flow, how to run, tests, demo, limitations.
- docs: SERVICE_DESIGN, IMPLEMENTATION_REFERENCE, PROJECT_DECISION_RECORD.

---

## Future ideas (not on the roadmap)

Optional enhancements if you extend the project later:

- PDF report export.
- Streamlit Cloud–style one-click deploy (alternative to VPS path in `DEPLOYMENT_ROADMAP.md`).
- Default options via config file (YAML/JSON).
- Rotating file logs in addition to current logging.
