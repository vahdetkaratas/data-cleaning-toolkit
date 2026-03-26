from pathlib import Path

import pandas as pd

from src.load import load_table, load_demo_sales, load_demo_customer


def test_load_demo_sales_shape_and_columns():
    df = load_demo_sales()
    assert not df.empty
    for col in ["order_id", "order_date", "product_id", "amount", "quantity", "region", "customer_id"]:
        assert col in df.columns


def test_load_demo_customer_shape_and_columns():
    df = load_demo_customer()
    assert not df.empty
    for col in ["customer_id", "signup_date", "segment", "lifetime_value", "tenure"]:
        assert col in df.columns


def test_load_table_csv_and_error_for_missing():
    path = Path("data/demo_sales/sales_messy.csv")
    df = load_table(path)
    assert isinstance(df, pd.DataFrame)
    try:
        load_table("data/does_not_exist.csv")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError for missing file")


def test_load_table_parquet(tmp_path: Path):
    """Load Parquet file returns DataFrame."""
    df_ref = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    p = tmp_path / "data.parquet"
    df_ref.to_parquet(p, index=False)
    df = load_table(p)
    assert len(df) == 2
    assert list(df.columns) == ["a", "b"]


def test_load_table_json(tmp_path: Path):
    """Load JSON file returns DataFrame."""
    p = tmp_path / "data.json"
    p.write_text('[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]', encoding="utf-8")
    df = load_table(p)
    assert len(df) == 2
    assert list(df.columns) == ["a", "b"]


def test_load_table_json_nested_flatten(tmp_path: Path):
    """Load JSON with nested dicts flattens one level (e.g. user.address -> user.address.city)."""
    p = tmp_path / "nested.json"
    p.write_text(
        '[{"id": 1, "name": "a", "meta": {"x": 10, "y": 20}}, {"id": 2, "name": "b", "meta": {"x": 30, "y": 40}}]',
        encoding="utf-8",
    )
    df = load_table(p)
    assert len(df) == 2
    assert "meta.x" in df.columns or "meta_x" in df.columns or "meta.x" in str(df.columns)
    assert "id" in df.columns and "name" in df.columns


def test_load_unsupported_format_raises():
    """Unsupported extension raises ValueError."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"a,b\n1,2")
        path = f.name
    try:
        try:
            load_table(path)
        except ValueError as e:
            assert "Unsupported" in str(e) or "txt" in str(e).lower()
            return
        raise AssertionError("Expected ValueError for .txt file")
    finally:
        Path(path).unlink(missing_ok=True)

