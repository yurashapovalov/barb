"""Single Barb Script tool for Anthropic Claude."""

import json
from pathlib import Path

from barb.interpreter import execute, QueryError

_EXPRESSIONS_MD = (Path(__file__).parent / "reference" / "expressions.md").read_text()

# Anthropic tool definition
BARB_TOOL = {
    "name": "run_query",
    "description": f"""Execute a Barb Script query against market data.

Query is a flat JSON object with these fields (all optional):
- session: "RTH" or "ETH" — filter by trading session (REQUIRED for daily+ timeframes)
- from: "1m", "5m", "15m", "30m", "1h", "daily", "weekly" — timeframe (default: "1m")
- period: "2024", "2024-03", "2024-01:2024-06", "last_year" — date filter
- map: {{"col_name": "expression"}} — compute derived columns
- where: "expression" — filter rows (boolean expression)
- group_by: "column" or ["col1", "col2"] — group rows (must be column name, not expression)
- select: "mean(col)" or ["sum(x)", "count()"] — aggregate functions
- sort: "column desc" or "column asc" — sort results
- limit: number — max rows to return

Execution order is FIXED: session → period → from → map → where → group_by → select → sort → limit

IMPORTANT:
- group_by requires a COLUMN NAME, not an expression. Create column in map first.
- select only supports: count(), sum(col), mean(col), min(col), max(col), std(col), median(col)
- For percentage calculations, run TWO queries: total count and filtered count.

{_EXPRESSIONS_MD}
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "object",
                "description": "Barb Script query object",
                "properties": {
                    "session": {"type": "string", "enum": ["RTH", "ETH"]},
                    "from": {"type": "string"},
                    "period": {"type": "string"},
                    "map": {"type": "object"},
                    "where": {"type": "string"},
                    "group_by": {},
                    "select": {},
                    "sort": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1},
                },
            },
        },
        "required": ["query"],
    },
}


def run_query(query: dict, df, sessions: dict) -> dict:
    """Execute Barb Script query and return structured result.

    Returns dict with:
        - model_response: str - compact summary for model
        - table: list | None - full data for UI
        - source_rows: list | None - evidence for aggregations
    """
    try:
        result = execute(query, df, sessions)
        summary = result.get("summary", {})

        return {
            "model_response": _format_summary_for_model(summary),
            "table": result.get("table"),
            "source_rows": result.get("source_rows"),
            "source_row_count": result.get("source_row_count"),
        }

    except QueryError as e:
        return {"model_response": f"Error: {e}", "table": None, "source_rows": None}
    except Exception as e:
        return {"model_response": f"Error: {type(e).__name__}: {e}", "table": None, "source_rows": None}


def _format_summary_for_model(summary: dict) -> str:
    """Format summary into compact string for model."""
    stype = summary.get("type", "unknown")

    if stype == "scalar":
        value = summary.get("value")
        rows_scanned = summary.get("rows_scanned")
        if rows_scanned:
            return f"Result: {value} (from {rows_scanned} rows)"
        return f"Result: {value}"

    if stype == "dict":
        values = summary.get("values", {})
        parts = [f"{k}={v}" for k, v in values.items()]
        return f"Result: {', '.join(parts)}"

    if stype == "table":
        lines = [f"Result: {summary.get('rows', 0)} rows"]

        # Stats
        if summary.get("stats"):
            for col, st in summary["stats"].items():
                if st.get("min") is not None:
                    mean_str = f", mean={st['mean']:.2f}" if st.get("mean") is not None else ""
                    lines.append(f"  {col}: min={st['min']}, max={st['max']}{mean_str}")

        # First/last
        if summary.get("first"):
            first_str = ", ".join(f"{k}={v}" for k, v in summary["first"].items())
            lines.append(f"  first: {first_str}")
        if summary.get("last"):
            last_str = ", ".join(f"{k}={v}" for k, v in summary["last"].items())
            lines.append(f"  last: {last_str}")

        return "\n".join(lines)

    if stype == "grouped":
        lines = [f"Result: {summary.get('rows', 0)} groups by {summary.get('by', '?')}"]

        # Min/max rows
        if summary.get("min_row"):
            min_parts = ", ".join(f"{k}={v}" for k, v in summary["min_row"].items())
            lines.append(f"  min: {min_parts}")
        if summary.get("max_row"):
            max_parts = ", ".join(f"{k}={v}" for k, v in summary["max_row"].items())
            lines.append(f"  max: {max_parts}")

        return "\n".join(lines)

    return f"Result: {summary}"
