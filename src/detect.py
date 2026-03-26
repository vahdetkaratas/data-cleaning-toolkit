from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from pandas.api import types as ptypes


MISSING_THRESHOLD_DEFAULT = 0.5


@dataclass
class ColumnIssueSummary:
    name: str
    dtype: str
    missing_ratio: float
    is_mostly_missing: bool
    invalid_format_count: int
    inconsistent_category_groups: int


def infer_column_types(
    df: pd.DataFrame,
    type_overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Very small heuristic type inference: numeric, date, categorical, text.
    type_overrides: optional dict mapping column name -> "date_candidate" | "numeric_candidate" to force type.
    """
    types: Dict[str, str] = {}
    overrides = type_overrides or {}
    for col in df.columns:
        if col in overrides:
            types[col] = overrides[col]
            continue
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            types[col] = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(s):
            types[col] = "date"
        else:
            lname = col.lower()
            if "date" in lname:
                types[col] = "date_candidate"
            elif any(key in lname for key in ["amount", "value", "price", "qty", "quantity", "tenure"]):
                types[col] = "numeric_candidate"
            else:
                types[col] = "categorical"
    return types


def _detect_invalid_formats(
    df: pd.DataFrame,
    inferred_types: Dict[str, str],
    date_formats: Optional[List[str]] = None,
) -> Dict[str, int]:
    """Return per-column invalid format counts for date/numeric candidates."""
    if date_formats is None:
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"]

    invalid_counts: Dict[str, int] = {}
    for col, kind in inferred_types.items():
        s = df[col]
        if kind in {"date", "date_candidate"}:
            # try multiple formats
            mask = s.notna()
            parsed_any: Optional[pd.Series] = None
            for fmt in date_formats:
                try:
                    parsed = pd.to_datetime(s, format=fmt, errors="coerce")
                except (TypeError, ValueError):
                    continue
                if parsed_any is None:
                    parsed_any = parsed
                else:
                    # combine: where previous NaT and new valid, take new
                    parsed_any = parsed_any.fillna(parsed)
            if parsed_any is None:
                invalid_counts[col] = 0
            else:
                invalid = mask & parsed_any.isna()
                invalid_counts[col] = int(invalid.sum())
        elif kind == "numeric_candidate":
            mask = s.notna()
            coerced = pd.to_numeric(s, errors="coerce")
            invalid = mask & coerced.isna()
            invalid_counts[col] = int(invalid.sum())
    return invalid_counts


def _detect_inconsistent_categories(df: pd.DataFrame) -> Dict[str, int]:
    """
    For object columns, count groups of values that differ only by case/whitespace.
    Returns number of such groups per column.
    """
    result: Dict[str, int] = {}
    for col in df.columns:
        s = df[col]
        if not (
            ptypes.is_object_dtype(s)
            or ptypes.is_string_dtype(s)
            or isinstance(s.dtype, pd.CategoricalDtype)
        ):
            continue
        values = s.dropna().astype(str)
        if values.empty:
            result[col] = 0
            continue
        groups: Dict[str, set] = {}
        for val in values.unique():
            key = val.strip().lower()
            groups.setdefault(key, set()).add(val)
        inconsistent_groups = sum(1 for vset in groups.values() if len(vset) > 1)
        result[col] = inconsistent_groups
    return result


def _detect_outliers_iqr(df: pd.DataFrame, inferred_types: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """For numeric columns, count values outside 1.5*IQR. Returns {col: {"count": int, "method": "IQR"}}."""
    result: Dict[str, Dict[str, Any]] = {}
    for col in df.columns:
        kind = inferred_types.get(col, "")
        if kind not in ("numeric", "numeric_candidate"):
            continue
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((s < low) | (s > high)).sum())
        if count > 0:
            result[col] = {"count": count, "method": "IQR"}
    return result


def _duplicate_subset(df: pd.DataFrame, key_columns: Optional[List[str]] = None) -> Optional[List[str]]:
    """Return subset of columns to use for duplicate detection; None means full row."""
    if key_columns is not None:
        # Empty list is treated as "use full row" to avoid pandas errors.
        if len(key_columns) == 0:
            return None
        missing = [c for c in key_columns if c not in df.columns]
        if missing:
            raise ValueError(
                "Invalid duplicate key columns provided. Missing columns: "
                + ", ".join(missing)
                + ". Leave 'Duplicate key columns' empty to auto-detect."
            )
        # Preserve user-specified order.
        return list(key_columns)
    if "order_id" in df.columns:
        return ["order_id"]
    if "customer_id" in df.columns:
        return ["customer_id"]
    return None


def detect_issues(
    df: pd.DataFrame,
    missing_threshold: float = MISSING_THRESHOLD_DEFAULT,
    key_columns: Optional[List[str]] = None,
    type_overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    High-level issue detection entrypoint.

    key_columns: optional list of column names to use for duplicate detection.
    type_overrides: optional dict mapping column name -> "date_candidate" | "numeric_candidate" to override inference.

    Returns a dict with:
    - schema: inferred types and dtypes
    - missing: per-column missing ratios + flag for mostly missing
    - duplicates: duplicate row count
    - invalid_formats: per-column invalid format counts (dates, numeric candidates)
    - inconsistent_categories: per-column count of case/whitespace-inconsistent groups
    - outliers: per-column outlier counts (numeric columns, IQR method)
    """
    n_rows = len(df)
    inferred_types = infer_column_types(df, type_overrides=type_overrides)

    # missing
    missing_ratios = df.isna().mean().to_dict() if n_rows > 0 else {c: 0.0 for c in df.columns}

    # duplicates: key_columns override, else order_id / customer_id / full row
    subset = _duplicate_subset(df, key_columns)
    if subset is not None:
        duplicate_count = int(df.duplicated(subset=subset).sum())
    else:
        duplicate_count = int(df.duplicated().sum())

    invalid_formats = _detect_invalid_formats(df, inferred_types)
    inconsistent_cats = _detect_inconsistent_categories(df)
    outliers = _detect_outliers_iqr(df, inferred_types)

    columns: List[ColumnIssueSummary] = []
    for col in df.columns:
        mr = float(missing_ratios.get(col, 0.0))
        columns.append(
            ColumnIssueSummary(
                name=col,
                dtype=str(df[col].dtype),
                missing_ratio=mr,
                is_mostly_missing=mr >= missing_threshold,
                invalid_format_count=invalid_formats.get(col, 0),
                inconsistent_category_groups=inconsistent_cats.get(col, 0),
            )
        )

    return {
        "n_rows": n_rows,
        "schema": {
            "inferred_types": inferred_types,
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        },
        "missing": {
            "missing_threshold": missing_threshold,
            "per_column": [
                {
                    "column": c.name,
                    "missing_ratio": np.round(c.missing_ratio, 4),
                    "is_mostly_missing": bool(c.is_mostly_missing),
                }
                for c in columns
            ],
        },
        "duplicates": {
            "duplicate_row_count": duplicate_count,
        },
        "invalid_formats": invalid_formats,
        "inconsistent_categories": inconsistent_cats,
        "outliers": outliers,
    }

