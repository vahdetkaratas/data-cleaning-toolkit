import io
import logging
import sys
from pathlib import Path

# Repo root on sys.path — required when Streamlit sets cwd/script path so
# `from src...` resolves (VPS, Docker, systemd, or running from another directory).
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from src.load import (
    CSV_ENCODING_FALLBACK,
    load_demo_customer,
    load_demo_sales,
    load_json_flattened_bytes,
)

logger = logging.getLogger(__name__)
from src.detect import _duplicate_subset, detect_issues
from src.clean import CleaningAction, basic_clean
from src.report import build_summary_table, report_to_bytes


MAX_UPLOAD_MB = 25
PREVIEW_HEAD_ROWS = 15
MAX_CHANGED_ROWS_SHOW = 12
MAX_INDEX_SCAN_FOR_CHANGES = 25_000


def _dup_key_hint(df: pd.DataFrame, key_columns: list | None) -> str:
    subset = _duplicate_subset(df, key_columns)
    if subset is None:
        return "Full row"
    return ", ".join(subset)


def _build_column_insights_df(
    df: pd.DataFrame,
    issues: dict,
    key_columns: list | None,
) -> pd.DataFrame:
    """Compact per-column view from detection output (before cleaning)."""
    subset = _duplicate_subset(df, key_columns)
    dup_key_set = set(subset) if subset else set()
    inv = issues.get("invalid_formats", {}) or {}
    inc = issues.get("inconsistent_categories", {}) or {}
    out = issues.get("outliers", {}) or {}
    missing_map = {m["column"]: m for m in issues.get("missing", {}).get("per_column", [])}
    rows = []
    for col in df.columns:
        m = missing_map.get(col, {})
        ratio = float(m.get("missing_ratio", 0.0))
        inv_c = int(inv.get(col, 0) or 0)
        inc_c = int(inc.get(col, 0) or 0)
        oi = out.get(col, {})
        out_c = int(oi.get("count", 0)) if isinstance(oi, dict) else 0
        role = "Key" if col in dup_key_set else "—"
        issue_parts = []
        if ratio > 0:
            issue_parts.append("missing")
        if inv_c > 0:
            issue_parts.append("parse")
        if inc_c > 0:
            issue_parts.append("category")
        if out_c > 0:
            issue_parts.append("outlier")
        rows.append(
            {
                "column": col,
                "missing %": round(ratio * 100, 2),
                "parse issues": inv_c,
                "category groups": inc_c,
                "outliers (IQR)": out_c,
                "dup. key": role,
                "flags": ", ".join(issue_parts) if issue_parts else "—",
            }
        )
    return pd.DataFrame(rows)


def _cleaning_summary_bullets(actions: list[CleaningAction]) -> list[str]:
    if not actions:
        return ["No cleaning steps produced changes (or all steps were disabled)."]
    return [a.description for a in actions]


def _sample_changed_row_indices(
    before: pd.DataFrame,
    after: pd.DataFrame,
    max_show: int = MAX_CHANGED_ROWS_SHOW,
    max_scan: int = MAX_INDEX_SCAN_FOR_CHANGES,
) -> tuple[list, str | None]:
    common = before.index.intersection(after.index)
    if common.empty:
        return [], "No overlapping row indices between before and after (rows were likely dropped or re-indexed)."
    changed: list = []
    note = None
    to_scan = list(common)
    if len(to_scan) > max_scan:
        to_scan = to_scan[:max_scan]
        note = f"Scanned first {max_scan:,} overlapping rows for cell-level changes."
    for idx in to_scan:
        if len(changed) >= max_show:
            break
        try:
            if not before.loc[idx].equals(after.loc[idx]):
                changed.append(idx)
        except (TypeError, ValueError, KeyError):
            continue
    return changed, note


def _read_uploaded_file(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    # Basic guardrail: very large uploads are rejected early to avoid timeouts/memory issues.
    file_size_mb = getattr(uploaded_file, "size", None)
    if file_size_mb is not None:
        file_size_mb = file_size_mb / (1024 * 1024)
        if file_size_mb > MAX_UPLOAD_MB:
            raise ValueError(
                f"File is too large ({file_size_mb:.1f} MB). "
                f"Please use a smaller file or sample (max ~{MAX_UPLOAD_MB} MB for demo use)."
            )

    if suffix == ".csv":
        data = uploaded_file.read()
        if not data.strip():
            raise ValueError("The file is empty.")
        last_err = None
        for enc in CSV_ENCODING_FALLBACK:
            try:
                df = pd.read_csv(io.BytesIO(data), encoding=enc, on_bad_lines="warn")
                if df.empty and len(df.columns) == 0:
                    raise ValueError("The file has no header or data rows.")
                return df
            except UnicodeDecodeError as e:
                last_err = e
                continue
            except pd.errors.EmptyDataError:
                raise ValueError("The file is empty or has no valid data.")
        raise ValueError(f"Could not decode the CSV (tried {CSV_ENCODING_FALLBACK}). Try saving as UTF-8.")
    if suffix in {".xls", ".xlsx"}:
        try:
            df = pd.read_excel(uploaded_file)
            if df.empty and len(df.columns) == 0:
                raise ValueError("The sheet is empty or has no data.")
            return df
        except Exception as e:
            if "EmptyDataError" in type(e).__name__ or "empty" in str(e).lower():
                raise ValueError("The Excel file or sheet is empty.")
            raise ValueError(f"Could not read Excel file. Check that the file is valid .xls/.xlsx. ({e})")
    if suffix == ".parquet":
        try:
            data = uploaded_file.read()
            return pd.read_parquet(io.BytesIO(data))
        except Exception as e:
            raise ValueError(f"Could not read Parquet file. ({e})")
    if suffix == ".json":
        try:
            data = uploaded_file.read()
            return load_json_flattened_bytes(data, lines=False)
        except Exception as e:
            raise ValueError(f"Could not read JSON file. ({e})")
    if suffix == ".jsonl":
        try:
            data = uploaded_file.read()
            return load_json_flattened_bytes(data, lines=True)
        except Exception as e:
            raise ValueError(f"Could not read JSONL file. ({e})")
    raise ValueError(f"Unsupported file type: {suffix}")


def main():
    st.set_page_config(page_title="Data Cleaning Toolkit", layout="wide")
    st.title("Data Cleaning Toolkit")
    st.write("Upload a CSV, Excel, Parquet, or JSON file or use one of the demo datasets to detect and fix basic data quality issues.")
    st.caption(
        "Quick start: choose a demo or upload files → set options in **2. Options** → run. "
        "**Issue summary** and **Column insights** show what was found; **Result** has previews and downloads."
    )

    if "data_key" not in st.session_state:
        st.session_state.data_key = None
        st.session_state.cached_df = None
        st.session_state.cached_source = None

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("1. Select data")
        uploaded = st.file_uploader(
            "Upload one or more files (CSV, Excel, Parquet, JSON)",
            type=["csv", "xls", "xlsx", "parquet", "json"],
            accept_multiple_files=True,
        )

        st.markdown("**Or use a demo dataset:**")
        demo_choice = st.radio(
            "Demo data",
            options=["None", "Sales (messy)", "Customer (messy)"],
            index=0,
            horizontal=True,
        )

        files_list = uploaded if isinstance(uploaded, list) else ([uploaded] if uploaded else [])
        data_key = (tuple(sorted(f.name for f in files_list)) if files_list else None, demo_choice)
        if data_key != st.session_state.data_key:
            df = None
            source_label = ""
            if files_list:
                try:
                    if len(files_list) == 1:
                        df = _read_uploaded_file(files_list[0])
                        source_label = files_list[0].name
                    else:
                        parts = []
                        for f in files_list:
                            d = _read_uploaded_file(f)
                            d["_source_file"] = f.name
                            parts.append(d)
                        df = pd.concat(parts, ignore_index=True)
                        source_label = f"Merged: {len(files_list)} files — {', '.join(f.name for f in files_list)}"
                except Exception as e:
                    logger.exception("Failed to read uploaded file(s)")
                    st.error(f"Failed to read file: {e}")
            elif demo_choice == "Sales (messy)":
                df = load_demo_sales()
                source_label = "demo_sales/sales_messy.csv"
            elif demo_choice == "Customer (messy)":
                df = load_demo_customer()
                source_label = "demo_customer/customer_messy.csv"
            st.session_state.data_key = data_key
            st.session_state.cached_df = df
            st.session_state.cached_source = source_label
        else:
            df = st.session_state.cached_df
            source_label = st.session_state.cached_source

        if df is None:
            st.info("Upload a file or choose a demo dataset to begin.")
            return

        n_rows, n_cols = len(df), len(df.columns)
        st.markdown(f"**Source:** `{source_label}` — {n_rows} rows, {n_cols} columns.")
        if n_rows > 100_000:
            st.warning(
                f"Large file ({n_rows:,} rows). Processing may be slow. Consider using a sample for a first check."
            )
        st.dataframe(df.head(), use_container_width=True)

    with col_right:
        st.subheader("2. Options")
        missing_threshold = st.slider(
            "Missing ratio threshold for warning (per column)",
            min_value=0.1,
            max_value=0.9,
            value=0.5,
            step=0.05,
        )
        key_columns_str = st.text_input(
            "Duplicate key columns (optional)",
            placeholder="e.g. order_id or customer_id, signup_date",
            help="Comma-separated column names to use for duplicate detection. Leave empty for auto (order_id / customer_id / full row). If any provided column is missing, the run stops with an error.",
        )
        key_columns = [c.strip() for c in key_columns_str.split(",") if c.strip()] if key_columns_str else None
        date_cols_str = st.text_input(
            "Columns to treat as date (optional)",
            placeholder="e.g. signup_date, created_at",
            help="Comma-separated. Overrides name-based inference.",
        )
        numeric_cols_str = st.text_input(
            "Columns to treat as numeric (optional)",
            placeholder="e.g. revenue, score",
            help="Comma-separated. Overrides name-based inference.",
        )
        type_overrides = {}
        for c in (date_cols_str or "").split(","):
            c = c.strip()
            if c:
                type_overrides[c] = "date_candidate"
        for c in (numeric_cols_str or "").split(","):
            c = c.strip()
            if c:
                type_overrides[c] = "numeric_candidate"
        type_overrides = type_overrides or None
        run_mode = st.radio(
            "Run mode",
            options=["Detect and clean", "Detect only"],
            index=0,
            help="Detect only: show issues without applying cleaning. Detect and clean: run full pipeline and download result.",
        )
        st.markdown("**Cleaning steps (when Detect and clean):**")
        drop_duplicates = st.checkbox("Drop duplicate rows", value=True)
        standardize_categories = st.checkbox("Standardize categories (case/whitespace)", value=True)
        coerce_numeric = st.checkbox("Coerce numeric columns", value=True)
        parse_dates = st.checkbox("Parse date columns", value=True)
        missing_choice = st.radio(
            "Missing values",
            options=["Leave as is", "Drop rows with missing", "Fill with value"],
            index=0,
            help="Leave: no change. Drop: remove rows that have any missing. Fill: replace missing with a value.",
        )
        missing_action = None
        fill_missing_value = 0
        if missing_choice == "Drop rows with missing":
            missing_action = "drop"
        elif missing_choice == "Fill with value":
            missing_action = "fill"
            fill_str = st.text_input("Fill value (e.g. 0 or empty)", value="0", key="fill_missing")
            try:
                fill_missing_value = int(fill_str)
            except ValueError:
                try:
                    fill_missing_value = float(fill_str)
                except ValueError:
                    fill_missing_value = "" if fill_str.strip() == "" else fill_str
        run_button = st.button("Run" if run_mode == "Detect only" else "Run detection & cleaning")

    if not run_button:
        return

    try:
        issues = detect_issues(
            df,
            missing_threshold=missing_threshold,
            key_columns=key_columns,
            type_overrides=type_overrides,
        )
    except ValueError as e:
        st.error(str(e))
        return
    detect_only = run_mode == "Detect only"

    if detect_only:
        cleaned = df
        actions = []
        summary = None
    else:
        try:
            cleaned, actions = basic_clean(
                df,
                drop_duplicates=drop_duplicates,
                standardize_categories=standardize_categories,
                coerce_numeric=coerce_numeric,
                parse_dates=parse_dates,
                missing_action=missing_action,
                fill_missing_value=fill_missing_value,
                duplicate_key_columns=key_columns,
                type_overrides=type_overrides,
            )
        except ValueError as e:
            st.error(str(e))
            return
        summary = build_summary_table(df, cleaned, issues, actions)

    st.markdown("---")
    st.subheader("3. Issue summary")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Missing per column**")
        missing_per = issues["missing"]["per_column"]
        if missing_per:
            st.dataframe(pd.DataFrame(missing_per), use_container_width=True)
        else:
            st.write("No missing values detected.")

        st.markdown("**Duplicates**")
        st.write(issues["duplicates"])

    with col_b:
        st.markdown("**Invalid formats (dates/numerics)**")
        st.json(issues.get("invalid_formats", {}))

        st.markdown("**Inconsistent categories (case/whitespace)**")
        st.json(issues.get("inconsistent_categories", {}))

        outliers = issues.get("outliers", {})
        if outliers:
            st.markdown("**Potential outliers (IQR)**")
            st.json(outliers)
        else:
            st.markdown("**Potential outliers (IQR)**")
            st.write("None detected.")

    st.subheader("3b. Column insights (before cleaning)")
    st.caption(
        f"Based on **detection only** (data **before** cleaning). "
        f"Duplicate logic uses: **{_dup_key_hint(df, key_columns)}**. "
        "“Key” = that column is part of the duplicate key (your list or built-in heuristic). "
        "Parse issues = non-empty values that did not match the tried date/numeric rules. "
        "Outlier counts are **IQR flags** in the report only; they are not auto-removed."
    )
    st.dataframe(
        _build_column_insights_df(df, issues, key_columns),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("4. Result")
    if detect_only:
        st.write("**Detect only** — no cleaning applied. Sample of current data:")
        st.dataframe(cleaned.head(PREVIEW_HEAD_ROWS), use_container_width=True)
    else:
        st.write(f"**Rows:** {summary['rows_before']:,} before → {summary['rows_after']:,} after cleaning.")

        st.markdown("**What cleaning did**")
        st.caption("Each bullet is the description recorded for a cleaning step (from the pipeline).")
        for bullet in _cleaning_summary_bullets(actions):
            st.markdown(f"- {bullet}")

        st.markdown("**Before / after preview (sample)**")
        st.caption(
            f"Left: first **{PREVIEW_HEAD_ROWS}** rows of the **original** table. "
            f"Right: first **{PREVIEW_HEAD_ROWS}** rows of the **cleaned** table. "
            "These sides are **not row-aligned by position** — after rows are dropped, “row 0” on the right is not the same logical row as “row 0” on the left. "
            "Use the section below for **same-index** comparisons where a row still exists."
        )
        prev_l, prev_r = st.columns(2)
        with prev_l:
            st.markdown("*Before (head)*")
            st.dataframe(df.head(PREVIEW_HEAD_ROWS), use_container_width=True)
        with prev_r:
            st.markdown("*After (head)*")
            st.dataframe(cleaned.head(PREVIEW_HEAD_ROWS), use_container_width=True)

        changed_idx, changed_note = _sample_changed_row_indices(df, cleaned)
        if changed_note:
            st.caption(changed_note)
        if changed_idx:
            st.markdown("**Same index: cells that changed (sample)**")
            st.caption(
                "Only rows that **still appear** in both tables with the **same index**. "
                "**Removed** rows (duplicates, drop-missing, etc.) are **not** listed here; they are no longer in the cleaned table."
            )
            ch_l, ch_r = st.columns(2)
            with ch_l:
                st.markdown("*Before*")
                st.dataframe(df.loc[changed_idx], use_container_width=True)
            with ch_r:
                st.markdown("*After*")
                st.dataframe(cleaned.loc[changed_idx], use_container_width=True)
        else:
            if summary["rows_after"] < summary["rows_before"]:
                st.caption(
                    "Row count dropped after cleaning — removed rows do not appear in a “same index” sample. "
                    "Compare the **head previews** above for a rough before/after feel, or download the full cleaned file."
                )
            else:
                st.caption(
                    "No cell-level differences found among **scanned** overlapping row indices, "
                    "or any change only removed rows (none left to compare by index in this sample)."
                )

        st.caption(
            "The HTML report includes the overview, issue tables, **schema comparison (before vs after)**, and cleaning actions."
        )
        export_format = st.radio("Export as", options=["CSV", "Parquet", "JSON"], index=0, horizontal=True)
        if export_format == "CSV":
            out_bytes = cleaned.to_csv(index=False).encode("utf-8")
            fname, mime = "cleaned_data.csv", "text/csv"
        elif export_format == "Parquet":
            buf = io.BytesIO()
            cleaned.to_parquet(buf, index=False)
            out_bytes = buf.getvalue()
            fname, mime = "cleaned_data.parquet", "application/octet-stream"
        else:
            out_bytes = cleaned.to_json(orient="records", date_format="iso").encode("utf-8")
            fname, mime = "cleaned_data.json", "application/json"
        st.download_button(
            f"Download cleaned ({export_format})",
            data=out_bytes,
            file_name=fname,
            mime=mime,
        )

        report_bytes = report_to_bytes(summary)
        st.download_button(
            "Download cleaning report (HTML)",
            data=report_bytes,
            file_name="cleaning_report.html",
            mime="text/html",
        )


if __name__ == "__main__":
    main()

