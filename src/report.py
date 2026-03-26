from __future__ import annotations

import html as html_module
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .clean import CleaningAction
from .schema import compare_schemas


def _escape(s: Any) -> str:
    """Escape string for safe HTML output (XSS prevention)."""
    if s is None:
        return ""
    return html_module.escape(str(s))


def build_summary_table(
    original: pd.DataFrame,
    cleaned: pd.DataFrame,
    issues: Dict[str, Any],
    actions: List[CleaningAction],
) -> Dict[str, Any]:
    """Return a JSON-serializable summary dict of key stats."""
    schema_diff = compare_schemas(original, cleaned, name_a="Before", name_b="After")
    return {
        "rows_before": len(original),
        "rows_after": len(cleaned),
        "columns": list(original.columns),
        "duplicates_dropped": issues.get("duplicates", {}).get("duplicate_row_count", 0),
        "missing": issues.get("missing", {}),
        "invalid_formats": issues.get("invalid_formats", {}),
        "inconsistent_categories": issues.get("inconsistent_categories", {}),
        "outliers": issues.get("outliers", {}),
        "schema_comparison": schema_diff,
        "cleaning_actions": [
            {"description": a.description, "details": a.details}
            for a in actions
        ],
    }


def render_html_report(summary: Dict[str, Any], title: str = "Data Cleaning Report") -> str:
    """Render a very small, self-contained HTML report from the summary dict."""
    rows_before = summary.get("rows_before", 0)
    rows_after = summary.get("rows_after", 0)
    duplicates_dropped = summary.get("duplicates_dropped", 0)
    missing = summary.get("missing", {})
    invalid_formats = summary.get("invalid_formats", {})
    inconsistent = summary.get("inconsistent_categories", {})
    outliers = summary.get("outliers", {})
    schema_cmp = summary.get("schema_comparison", {})
    actions = summary.get("cleaning_actions", [])

    def _dict_to_rows(d: Dict[str, Any]) -> str:
        parts = []
        for k, v in d.items():
            parts.append(f"<tr><td>{_escape(k)}</td><td>{_escape(v)}</td></tr>")
        return "\n".join(parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{_escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; line-height: 1.6; }}
    h1, h2 {{ margin-top: 1.4rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 0.5rem 0 1rem 0; }}
    th, td {{ border: 1px solid #ddd; padding: 0.35rem 0.5rem; font-size: 0.9rem; }}
    th {{ background: #f6f8fa; text-align: left; }}
    code {{ background: #f6f8fa; padding: 0.1em 0.3em; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>{_escape(title)}</h1>
  <h2>Overview</h2>
  <p>Rows before cleaning: <strong>{_escape(rows_before)}</strong><br>
     Rows after cleaning: <strong>{_escape(rows_after)}</strong><br>
     Duplicate rows dropped: <strong>{_escape(duplicates_dropped)}</strong></p>

  <h2>Missing Summary</h2>
  <table>
    <tr><th>Column</th><th>Missing ratio</th><th>Mostly missing?</th></tr>"""

    per_col = missing.get("per_column", [])
    for item in per_col:
        col = item.get("column")
        ratio = item.get("missing_ratio")
        flag = item.get("is_mostly_missing")
        html += f"\n    <tr><td>{_escape(col)}</td><td>{_escape(ratio)}</td><td>{_escape(flag)}</td></tr>"

    html += """
  </table>

  <h2>Invalid Formats</h2>
  <table>
    <tr><th>Column</th><th>Invalid count</th></tr>
"""
    html += _dict_to_rows(invalid_formats)
    html += """
  </table>

  <h2>Inconsistent Categories</h2>
  <table>
    <tr><th>Column</th><th>Inconsistent groups</th></tr>
"""
    html += _dict_to_rows(inconsistent)
    html += """
  </table>

  <h2>Potential outliers (IQR)</h2>
  <table>
    <tr><th>Column</th><th>Outlier count</th><th>Method</th></tr>
"""
    for col, info in outliers.items():
        if isinstance(info, dict):
            cnt = info.get("count", "")
            method = info.get("method", "IQR")
        else:
            cnt, method = info, "IQR"
        html += f"    <tr><td>{_escape(col)}</td><td>{_escape(cnt)}</td><td>{_escape(method)}</td></tr>\n"
    if not outliers:
        html += "    <tr><td colspan=\"3\">None detected.</td></tr>\n"
    html += """  </table>

  <h2>Schema comparison (Before vs After)</h2>
  <p><strong>"""
    html += _escape(schema_cmp.get("summary", "Same columns and dtypes"))
    html += """</strong></p>
  <table>
    <tr><th>Column</th><th>Before</th><th>After</th></tr>
"""
    for col, dtypes in schema_cmp.get("dtype_changes", {}).items():
        html += f"    <tr><td>{_escape(col)}</td><td>{_escape(dtypes.get('Before', ''))}</td><td>{_escape(dtypes.get('After', ''))}</td></tr>\n"
    only_before = schema_cmp.get("columns_only_in_a", [])
    only_after = schema_cmp.get("columns_only_in_b", [])
    for col in only_before:
        html += f"    <tr><td>{_escape(col)}</td><td>—</td><td><em>removed</em></td></tr>\n"
    for col in only_after:
        html += f"    <tr><td>{_escape(col)}</td><td><em>added</em></td><td>—</td></tr>\n"
    if not schema_cmp.get("dtype_changes") and not only_before and not only_after:
        html += "    <tr><td colspan=\"3\">No structural changes.</td></tr>\n"
    html += """  </table>

  <h2>Cleaning Actions</h2>
  <ul>
"""
    for a in actions:
        desc = _escape(a.get("description", ""))
        details_str = _escape(str(a.get("details", "")))
        html += f"    <li><strong>{desc}</strong> — <code>{details_str}</code></li>\n"

    html += """  </ul>
</body>
</html>
"""
    return html


def report_to_bytes(summary: Dict[str, Any], title: str = "Data Cleaning Report") -> bytes:
    """Render HTML report to UTF-8 bytes (e.g. for in-memory download, no disk write)."""
    return render_html_report(summary, title=title).encode("utf-8")


def save_html_report(summary: Dict[str, Any], output_path: Path | str) -> Path:
    """Render and save HTML report; return path."""
    html = render_html_report(summary)
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    return p

