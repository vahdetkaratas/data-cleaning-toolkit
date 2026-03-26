# Improvements, Weaknesses & Risks

A concise critique and prioritized recommendations for the Data Cleaning Toolkit.

**Recently implemented (2025-03):** Encoding, 100K warning, duplicate key, detect-only mode, upload errors, session state, type override, outlier warning, integration test; then logging (load/app), report stream download (`report_to_bytes`), portfolio screenshots note. See CHANGELOG for details.

---

## 1. Weaknesses & risks

### High impact

| Issue | Risk | Where |
|-------|------|--------|
| ~~**CSV encoding not set**~~ | *Fixed:* CSV tries utf-8, cp1252, latin1; optional `encoding=` in `load_table()`. Upload uses same fallback. | `load.py`, `app.py` |
| ~~**No size limit on upload**~~ | *Fixed:* README recommends max ~100K rows; app shows a warning when rows > 100K. | `README.md`, `app.py` |
| ~~**Type inference is name-based**~~ | *Mitigated:* Optional "Columns as date" / "Columns as numeric" in UI (`type_overrides`); overrides name-based inference. | `detect.py`, `clean.py`, `app.py` |

### Medium impact

| Issue | Risk | Where |
|-------|------|--------|
| ~~**Advanced options not in UI**~~ | *Fixed:* Optional "Duplicate key columns" input; passed to detect and clean. | `app.py` |
| ~~**No “detect only” mode**~~ | *Fixed:* Run mode “Detect only” vs “Detect and clean” in app. | `app.py` |
| ~~**Generic error handling**~~ | *Fixed:* Empty file, encoding, Excel errors show short user-facing messages; CSV encoding fallback on upload. | `app.py` |
| ~~**No logging**~~ | *Fixed:* load.py and app log file-not-found, decode failures, and upload read errors. | `load.py`, `app.py` |

### Lower impact

| Issue | Risk | Where |
|-------|------|--------|
| ~~**Streamlit full re-run**~~ | *Mitigated:* Loaded df and source cached in `st.session_state`; only reload when file/demo choice changes. | `app.py` |
| ~~**Report written to disk then read**~~ | *Fixed:* Report generated in memory (`report_to_bytes`) and passed to download button; no disk write/read for download. | `report.py`, `app.py` |
| ~~**No automated tests for the app**~~ | Only `src` and report are tested. No Streamlit or end-to-end test (e.g. “upload CSV → run → check report exists”). | `tests/` |

---

## 2. Recommendations

All items above have been addressed (see CHANGELOG and V2_ROADMAP). Optional for future: PDF report, Streamlit Cloud deploy, config file, log file.

---

## 3. What is already solid

- Clear separation: load → detect → clean → report; easy to extend.
- HTML report escaping (XSS) and pandas deprecation fixes in place.
- Column-level control in the API (opt-in/opt-out standardization, duplicate key).
- Docs and structure are consistent and GitHub-ready.
- Tests cover core logic and edge cases (empty df, key_columns, escape).

---

## 4. One-line summary

**Status:** All listed improvements are implemented (encoding, size warning, duplicate key, detect-only mode, upload errors, session state, type override, outlier warning, integration test, logging, report stream; V2: Parquet/JSON, outliers in report, user cleaning rules, schema comparison, multi-file merge). Optional for later: PDF report, deploy, config file.
