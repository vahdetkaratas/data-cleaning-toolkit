import json
import logging
from pathlib import Path
from typing import Any, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


PathLike = Union[str, Path]

# Try these encodings in order when reading CSV (Excel-saved files often use cp1252)
CSV_ENCODING_FALLBACK: List[str] = ["utf-8", "cp1252", "latin1"]


def _has_nested_dict(obj: Any) -> bool:
    """Return True if obj is a dict that has at least one value that is a dict or list."""
    if not isinstance(obj, dict):
        return False
    for v in obj.values():
        if isinstance(v, (dict, list)):
            return True
    return False


def _project_root() -> Path:
    # src/load.py -> src -> project root (parent of src/)
    return Path(__file__).resolve().parents[1]


def _load_json_flatten_from_text(text: str, lines: bool = False) -> pd.DataFrame:
    """Parse JSON/JSONL text and flatten one level of nested dicts if present."""
    if lines:
        data: List[Any] = []
        for line in text.strip().splitlines():
            if line.strip():
                data.append(json.loads(line))
        if not data:
            return pd.DataFrame()
    else:
        data = json.loads(text)
        if not isinstance(data, list):
            data = [data] if isinstance(data, dict) else []

    if not data or not isinstance(data[0], dict):
        return pd.DataFrame(data) if data else pd.DataFrame()
    if _has_nested_dict(data[0]):
        return pd.json_normalize(data)
    return pd.DataFrame(data)


def _load_json_flatten(path: Path, lines: bool = False) -> pd.DataFrame:
    """Load JSON or JSONL from disk and flatten one level of nested dicts if present."""
    return _load_json_flatten_from_text(path.read_text(encoding="utf-8"), lines=lines)


def load_json_flattened_bytes(raw: bytes, lines: bool = False) -> pd.DataFrame:
    """Load JSON/JSONL from uploaded bytes with the same flattening rules as `load_table()`."""
    text = raw.decode("utf-8")
    return _load_json_flatten_from_text(text, lines=lines)


def load_table(
    path: PathLike,
    encoding: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load CSV, Excel, Parquet, or JSON file into a pandas DataFrame.

    - CSV: tries encodings utf-8, cp1252, latin1 (use encoding= to force one).
    - Excel: .xls, .xlsx (requires openpyxl).
    - Parquet: .parquet (requires pyarrow).
    - JSON: .json (array of objects) or .jsonl (lines) (encoding ignored for binary parquet).
    """
    p = Path(path)
    if not p.is_absolute():
        p = _project_root() / p
    if not p.exists():
        logger.error("File not found: %s", p)
        raise FileNotFoundError(f"File not found: {p}")
    suffix = p.suffix.lower()
    if suffix == ".csv":
        encodings = [encoding] if encoding else CSV_ENCODING_FALLBACK
        last_error: Optional[Exception] = None
        for enc in encodings:
            if enc is None:
                continue
            try:
                return pd.read_csv(p, encoding=enc, on_bad_lines="warn")
            except UnicodeDecodeError as e:
                last_error = e
                continue
        logger.warning("CSV decode failed with encodings %s: %s", encodings, last_error)
        raise ValueError(f"Could not decode CSV with encodings {encodings}: {last_error}")
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(p)
    if suffix == ".parquet":
        return pd.read_parquet(p)
    if suffix == ".json":
        return _load_json_flatten(p, lines=False)
    if suffix == ".jsonl":
        return _load_json_flatten(p, lines=True)
    raise ValueError(f"Unsupported file type: {suffix}")


def load_demo_sales() -> pd.DataFrame:
    """Convenience helper for demo_sales/sales_messy.csv."""
    return load_table(Path("data/demo_sales/sales_messy.csv"))


def load_demo_customer() -> pd.DataFrame:
    """Convenience helper for demo_customer/customer_messy.csv."""
    return load_table(Path("data/demo_customer/customer_messy.csv"))

