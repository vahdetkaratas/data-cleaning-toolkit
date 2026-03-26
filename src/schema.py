"""Schema comparison utilities for Data Cleaning Toolkit."""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def compare_schemas(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    name_a: str = "A",
    name_b: str = "B",
) -> Dict[str, Any]:
    """
    Compare two DataFrames by column presence and dtypes.

    Returns a dict with:
    - columns_only_in_a: list of column names
    - columns_only_in_b: list of column names
    - common_columns: list of column names in both
    - dtype_changes: for common columns, {col: {"a": str(dtype), "b": str(dtype)} if different
    - summary: short string summary
    """
    cols_a = set(df_a.columns)
    cols_b = set(df_b.columns)
    only_a = sorted(cols_a - cols_b)
    only_b = sorted(cols_b - cols_a)
    common = sorted(cols_a & cols_b)

    dtype_changes: Dict[str, Dict[str, str]] = {}
    for col in common:
        dt_a = str(df_a[col].dtype)
        dt_b = str(df_b[col].dtype)
        if dt_a != dt_b:
            dtype_changes[col] = {name_a: dt_a, name_b: dt_b}

    summary_parts: List[str] = []
    if only_a:
        summary_parts.append(f"Only in {name_a}: {len(only_a)}")
    if only_b:
        summary_parts.append(f"Only in {name_b}: {len(only_b)}")
    if dtype_changes:
        summary_parts.append(f"Dtype changes: {len(dtype_changes)}")
    if not summary_parts:
        summary_parts.append("Same columns and dtypes")

    return {
        "columns_only_in_a": only_a,
        "columns_only_in_b": only_b,
        "common_columns": common,
        "dtype_changes": dtype_changes,
        "summary": "; ".join(summary_parts),
    }
