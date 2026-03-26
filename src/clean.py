from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pandas.api import types as ptypes

from .detect import _duplicate_subset, infer_column_types


@dataclass
class CleaningAction:
    description: str
    details: Dict[str, Any]


def _standardize_categories(series: pd.Series) -> Tuple[pd.Series, Dict[str, str]]:
    """
    Standardize categorical values by lowercasing/stripping and taking first seen
    representation as canonical. Returns new series and mapping dict.
    """
    mapping: Dict[str, str] = {}
    result = []
    for val in series:
        if pd.isna(val):
            result.append(val)
            continue
        sval = str(val)
        key = sval.strip().lower()
        if key not in mapping:
            mapping[key] = sval.strip()
        result.append(mapping[key])
    return pd.Series(result, index=series.index), mapping


def basic_clean(
    df: pd.DataFrame,
    *,
    drop_duplicates: bool = True,
    standardize_categories: bool = True,
    coerce_numeric: bool = True,
    parse_dates: bool = True,
    missing_action: Optional[str] = None,
    fill_missing_value: Any = 0,
    standardize_only_columns: Optional[List[str]] = None,
    skip_standardize_columns: Optional[List[str]] = None,
    duplicate_key_columns: Optional[List[str]] = None,
    type_overrides: Optional[Dict[str, str]] = None,
) -> Tuple[pd.DataFrame, List[CleaningAction]]:
    """
    Apply a simple, opinionated cleaning pipeline. Each step can be turned off via flags.

    - drop_duplicates: drop duplicate rows (when True).
    - standardize_categories: standardize case/whitespace for object columns (when True).
    - coerce_numeric: convert numeric_candidate columns to numeric (when True).
    - parse_dates: parse date_candidate columns to datetime (when True).
    - missing_action: None/"leave" = leave missing as is; "drop" = drop rows with any missing; "fill" = fill with fill_missing_value.
    - fill_missing_value: value used when missing_action == "fill" (default 0).
    """
    actions: List[CleaningAction] = []
    cleaned = df.copy()

    # 0) Missing values: leave / drop rows / fill with value
    if missing_action == "drop":
        before = len(cleaned)
        cleaned = cleaned.dropna()
        dropped = before - len(cleaned)
        if dropped > 0:
            actions.append(
                CleaningAction(
                    description="Dropped rows with missing values",
                    details={"before": before, "after": len(cleaned), "dropped": dropped},
                )
            )
    elif missing_action == "fill":
        cleaned = cleaned.fillna(fill_missing_value)
        actions.append(
            CleaningAction(
                description="Filled missing values",
                details={"value": str(fill_missing_value)},
            )
        )

    # 1) Drop duplicates
    if drop_duplicates:
        before = len(cleaned)
        subset = _duplicate_subset(cleaned, duplicate_key_columns)
        if subset is not None:
            cleaned = cleaned.drop_duplicates(subset=subset)
        else:
            cleaned = cleaned.drop_duplicates()
        after = len(cleaned)
        if after < before:
            actions.append(
                CleaningAction(
                    description="Dropped duplicate rows",
                    details={"before": before, "after": after, "dropped": before - after},
                )
            )

    # 2) Infer types (with optional overrides)
    inferred = infer_column_types(cleaned, type_overrides=type_overrides)

    # 3) Standardize categorical/text columns
    skip_set = set(skip_standardize_columns or [])
    only_set = set(standardize_only_columns or []) if standardize_only_columns else None

    if standardize_categories:
        for col in cleaned.columns:
            s = cleaned[col]
            if not (
                ptypes.is_object_dtype(s)
                or ptypes.is_string_dtype(s)
                or isinstance(s.dtype, pd.CategoricalDtype)
            ):
                continue
            if col in skip_set:
                continue
            if only_set is not None and col not in only_set:
                continue
            new_col, mapping = _standardize_categories(cleaned[col])
            cleaned[col] = new_col
            if mapping and len(mapping) > 0:
                actions.append(
                    CleaningAction(
                        description=f"Standardized categorical values in '{col}'",
                        details={"unique_groups": len(mapping)},
                    )
                )

    # 4) Convert numeric_candidate/string numerics to actual numeric
    if coerce_numeric:
        for col, kind in inferred.items():
            if kind == "numeric_candidate" and pd.api.types.is_object_dtype(cleaned[col]):
                before_non_na = cleaned[col].notna().sum()
                converted = pd.to_numeric(cleaned[col], errors="coerce")
                cleaned[col] = converted
                after_non_na = converted.notna().sum()
                actions.append(
                    CleaningAction(
                        description=f"Converted '{col}' to numeric",
                        details={
                            "non_na_before": int(before_non_na),
                            "non_na_after": int(after_non_na),
                        },
                    )
                )

    # 5) Parse date/date_candidate columns
    if parse_dates:
        date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"]
        for col, kind in inferred.items():
            if kind not in {"date", "date_candidate"}:
                continue
            s = cleaned[col]
            best = None
            for fmt in date_formats:
                try:
                    parsed = pd.to_datetime(s, format=fmt, errors="coerce")
                except (TypeError, ValueError):
                    continue
                if best is None:
                    best = parsed
                else:
                    best = best.fillna(parsed)
            if best is not None:
                cleaned[col] = best
                actions.append(
                    CleaningAction(
                        description=f"Parsed '{col}' as datetime",
                        details={"non_na": int(best.notna().sum())},
                    )
                )

    return cleaned, actions

