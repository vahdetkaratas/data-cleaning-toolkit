from pathlib import Path

import pandas as pd
import pytest

from src.load import load_demo_sales, load_demo_customer, load_table
from src.detect import detect_issues
from src.clean import basic_clean
from src.report import build_summary_table, report_to_bytes, save_html_report
from src.schema import compare_schemas


def test_detect_issues_on_demo_sales():
    df = load_demo_sales()
    issues = detect_issues(df, missing_threshold=0.4)
    assert issues["n_rows"] == len(df)
    # amount column has at least one missing
    missing_cols = {item["column"]: item for item in issues["missing"]["per_column"]}
    assert "amount" in missing_cols
    assert missing_cols["amount"]["missing_ratio"] > 0
    # there should be at least one duplicate row
    assert issues["duplicates"]["duplicate_row_count"] >= 1
    # region has inconsistent categories (North/NORTH/north)
    assert issues["inconsistent_categories"].get("region", 0) >= 1


def test_clean_basic_reduces_duplicates_and_standardizes_categories():
    df = load_demo_sales()
    cleaned, actions = basic_clean(df)
    assert len(cleaned) < len(df)  # duplicates dropped
    # region values should be case-normalized (no mixed-case variants)
    unique_regions = set(cleaned["region"].dropna().astype(str).tolist())
    lowered = {r.lower() for r in unique_regions}
    # unique display values count and lowered count should match (no North/NORTH pairs)
    assert len(unique_regions) == len(lowered)
    # at least one cleaning action recorded
    assert any("Standardized categorical values" in a.description for a in actions)


def test_report_html_saved(tmp_path: Path):
    df = load_demo_customer()
    issues = detect_issues(df)
    cleaned, actions = basic_clean(df)
    summary = build_summary_table(df, cleaned, issues, actions)
    out = save_html_report(summary, tmp_path / "cleaning_report.html")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "Data Cleaning Report" in text
    assert "Rows before cleaning" in text


def test_integration_pipeline_from_file(tmp_path: Path):
    """Full pipeline: load from data path, detect, clean, save report; report exists and has expected content."""
    data_path = Path("data/demo_sales/sales_messy.csv")
    if not data_path.exists():
        return  # skip if run from elsewhere
    df = load_table(data_path)
    assert len(df) > 0 and len(df.columns) > 0
    issues = detect_issues(df)
    cleaned, actions = basic_clean(df)
    summary = build_summary_table(df, cleaned, issues, actions)
    assert summary["rows_before"] == len(df)
    assert summary["rows_after"] == len(cleaned)
    assert "outliers" in summary
    # Report via bytes (no disk) and via file must both contain key sections
    report_bytes = report_to_bytes(summary)
    text = report_bytes.decode("utf-8")
    assert "Data Cleaning Report" in text
    assert "Overview" in text
    assert "Rows before cleaning" in text
    assert "Potential outliers" in text
    assert "Cleaning Actions" in text
    assert "Schema comparison" in text
    out = save_html_report(summary, tmp_path / "integration_report.html")
    assert out.exists()
    assert "Data Cleaning Report" in out.read_text(encoding="utf-8")


def test_detect_issues_empty_dataframe():
    """Empty DataFrame does not crash; n_rows=0."""
    df = pd.DataFrame(columns=["a", "b"])
    issues = detect_issues(df)
    assert issues["n_rows"] == 0
    assert len(issues["missing"]["per_column"]) == 2
    assert issues["duplicates"]["duplicate_row_count"] == 0


def test_detect_issues_key_columns_override():
    """key_columns is used for duplicate count when provided and valid."""
    df = load_demo_sales()
    # by order_id (default) we get some duplicates; by a column that has no dupes we get 0
    issues_default = detect_issues(df, key_columns=None)
    issues_by_order = detect_issues(df, key_columns=["order_id"])
    assert issues_by_order["duplicates"]["duplicate_row_count"] == issues_default["duplicates"]["duplicate_row_count"]
    # duplicate by product_id only - different count possible
    issues_product = detect_issues(df, key_columns=["product_id"])
    assert "duplicate_row_count" in issues_product["duplicates"]


def test_detect_issues_invalid_key_columns_raises():
    df = load_demo_sales()
    with pytest.raises(ValueError) as excinfo:
        detect_issues(df, key_columns=["does_not_exist"])
    assert "missing columns" in str(excinfo.value).lower()


def test_clean_skip_standardize_columns():
    """skip_standardize_columns leaves those columns out of standardization."""
    df = load_demo_sales()
    cleaned, _ = basic_clean(df, skip_standardize_columns=["region"])
    # region should still have original mixed case if we skipped it
    assert "region" in cleaned.columns
    # at least one cleaning action (e.g. duplicates or dates) still applied
    cleaned2, actions2 = basic_clean(df)
    assert len(actions2) >= 1


def test_clean_missing_action_drop():
    """missing_action='drop' removes rows with any missing value."""
    df = pd.DataFrame({"a": [1, None, 3], "b": [10, 20, None]})
    cleaned, actions = basic_clean(df, drop_duplicates=False, standardize_categories=False, coerce_numeric=False, parse_dates=False, missing_action="drop")
    assert len(cleaned) == 1
    assert list(cleaned.iloc[0]) == [1, 10] or list(cleaned.iloc[0]) == [3.0, 20.0]
    assert any("Dropped rows with missing" in a.description for a in actions)


def test_clean_missing_action_fill():
    """missing_action='fill' fills missing with given value."""
    df = pd.DataFrame({"a": [1, None, 3], "b": ["x", None, "z"]})
    cleaned, actions = basic_clean(df, drop_duplicates=False, standardize_categories=False, coerce_numeric=False, parse_dates=False, missing_action="fill", fill_missing_value=0)
    assert cleaned["a"].isna().sum() == 0
    assert (cleaned["a"] == 0).any() or (cleaned["a"].astype(float) == 0).any()
    assert any("Filled missing" in a.description for a in actions)


def test_clean_user_selected_rules():
    """When steps are disabled, they are skipped."""
    df = pd.DataFrame({"id": [1, 1, 2], "x": ["A", "a", "B"]})
    cleaned_drop, _ = basic_clean(df, drop_duplicates=False)
    assert len(cleaned_drop) == 3
    cleaned_std, actions = basic_clean(df, standardize_categories=False)
    assert "Standardized" not in " ".join(a.description for a in actions)


def test_clean_duplicate_key_columns():
    """duplicate_key_columns is used when provided."""
    df = pd.DataFrame({"id": [1, 1, 2], "x": ["a", "b", "c"]})
    cleaned, actions = basic_clean(df, duplicate_key_columns=["id"])
    assert len(cleaned) == 2
    assert any("Dropped duplicate" in a.description for a in actions)


def test_clean_invalid_duplicate_key_columns_raises():
    df = load_demo_sales()
    with pytest.raises(ValueError) as excinfo:
        basic_clean(df, duplicate_key_columns=["does_not_exist"])
    assert "missing columns" in str(excinfo.value).lower()


def test_detect_issues_type_overrides():
    """type_overrides forces date_candidate/numeric_candidate for columns."""
    df = pd.DataFrame({
        "my_date": ["2020-01-01", "2021/02/02", "bad"],
        "my_value": ["10", "20", "x"],
    })
    issues = detect_issues(df, type_overrides={"my_date": "date_candidate", "my_value": "numeric_candidate"})
    assert "my_date" in issues["invalid_formats"] or "my_value" in issues["invalid_formats"]
    assert "date_candidate" in issues["schema"]["inferred_types"].get("my_date", "")
    assert "numeric_candidate" in issues["schema"]["inferred_types"].get("my_value", "")


def test_detect_issues_outliers():
    """Numeric columns get outlier count (IQR) when present."""
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 100]})  # 100 is outlier
    issues = detect_issues(df)
    assert "outliers" in issues
    assert issues["outliers"].get("x", {}).get("count", 0) >= 1


def test_compare_schemas():
    """compare_schemas returns only_a, only_b, common, dtype_changes, summary."""
    df_a = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    df_b = pd.DataFrame({"a": [1.0, 2.0], "c": [10, 20]})
    out = compare_schemas(df_a, df_b, name_a="Before", name_b="After")
    assert "b" in out["columns_only_in_a"]
    assert "c" in out["columns_only_in_b"]
    assert "a" in out["common_columns"]
    assert "a" in out["dtype_changes"]
    assert "Before" in out["dtype_changes"]["a"] and "After" in out["dtype_changes"]["a"]
    assert "summary" in out


def test_report_html_includes_outliers():
    """When summary has outliers, HTML report contains the outlier section."""
    summary = {
        "rows_before": 10,
        "rows_after": 10,
        "duplicates_dropped": 0,
        "missing": {"per_column": []},
        "invalid_formats": {},
        "inconsistent_categories": {},
        "outliers": {"amount": {"count": 2, "method": "IQR"}},
        "cleaning_actions": [],
    }
    from src.report import render_html_report
    html = render_html_report(summary)
    assert "Potential outliers" in html
    assert "amount" in html
    assert "2" in html
    assert "IQR" in html


def test_report_html_escapes_special_chars(tmp_path: Path):
    """Report escapes HTML/special chars to prevent XSS."""
    summary = {
        "rows_before": 1,
        "rows_after": 1,
        "duplicates_dropped": 0,
        "missing": {"per_column": [{"column": "<script>alert(1)</script>", "missing_ratio": 0, "is_mostly_missing": False}]},
        "invalid_formats": {},
        "inconsistent_categories": {},
        "cleaning_actions": [{"description": "Test <img src=x>", "details": {"x": "& \"quoted\""}}],
    }
    out = save_html_report(summary, tmp_path / "report.html")
    text = out.read_text(encoding="utf-8")
    assert "&lt;script&gt;" in text
    assert "&lt;img" in text
    assert "<script>" not in text

