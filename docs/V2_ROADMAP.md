# V2 Roadmap — Data Cleaning Toolkit

Short roadmap status for GitHub readability.

---

## Status Snapshot

| Area | Status | Version |
|------|--------|---------|
| Outliers in HTML report | Done | 2.0.0 |
| Integration pipeline test (app logic path) | Done | 2.0.0 |
| Parquet/JSON load + export options | Done | 2.0.0 |
| User-selected cleaning steps | Done | 2.0.0 |
| Schema comparison (before vs after) | Done | 2.0.0 |
| Multi-file merge preview (concat + `_source_file`) | Done | 2.0.0 |
| Missing handling: leave / drop / fill | Done | 2.1.0 |
| Nested JSON flatten (one level) | Done | 2.1.0 |

---

## Implemented Scope (2.0.0 / 2.1.0)

- Input: CSV, Excel, Parquet, JSON/JSONL.
- Processing: detect, clean, report, schema compare.
- UI: detect-only mode, advanced cleaning options, missing handling, multi-file upload, column insights, before/after previews, cleaning summary bullets.
- Output: cleaned CSV/Parquet/JSON + HTML report.
- Reliability: integration and unit tests for core paths.

---

## Optional Next (Not Yet Implemented)

- PDF report export.
- Streamlit Cloud deployment.
- Config file support (YAML/JSON defaults).
- Log-to-file support (rotating file logs).

---

## Notes

- Detailed release history is in `docs/CHANGELOG.md`.
- Technical details are in `docs/IMPLEMENTATION_REFERENCE.md`.
