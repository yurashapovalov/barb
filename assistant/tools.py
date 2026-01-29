"""Tool definitions and execution for the LLM assistant.

Two tools for v1:
- execute_query: runs a Barb Script query against OHLCV data
- get_query_reference: returns the Barb Script format reference
"""

import json
import logging

import pandas as pd

from barb.interpreter import execute, QueryError

log = logging.getLogger(__name__)


# --- Tool declarations (Gemini function calling format) ---

EXECUTE_QUERY_DECLARATION = {
    "name": "execute_query",
    "description": (
        "Execute a Barb Script query on historical OHLCV minute data. "
        "Returns the result (scalar or table) with metadata. "
        "Call get_query_reference first to learn the query format."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "object",
                "description": "Barb Script query object",
                "properties": {
                    "session": {
                        "type": "string",
                        "description": "Trading session filter: RTH, ETH, OVERNIGHT, ASIAN, EUROPEAN, etc.",
                    },
                    "from": {
                        "type": "string",
                        "description": "Timeframe: 1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly",
                    },
                    "period": {
                        "type": "string",
                        "description": "Date filter: '2024', '2024-03', '2024-01-01:2024-06-30', 'last_year', 'last_month', 'last_week'",
                    },
                    "map": {
                        "type": "object",
                        "description": "Derived columns. Each key is a column name, each value MUST be a plain string expression like \"high - low\". Never use nested objects.",
                    },
                    "where": {
                        "type": "string",
                        "description": "Row filter expression. Example: 'close > open and volume > 1000'",
                    },
                    "group_by": {
                        "type": "string",
                        "description": "Group by column name. Example: 'weekday'",
                    },
                    "select": {
                        "type": "string",
                        "description": "Aggregate expression. Example: 'mean(range)', 'count()'",
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort: 'column_name asc' or 'column_name desc'",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max rows to return",
                    },
                },
            },
        },
        "required": ["query"],
    },
}

GET_QUERY_REFERENCE_DECLARATION = {
    "name": "get_query_reference",
    "description": (
        "Get the Barb Script query format reference: "
        "all fields, functions, expressions, and examples. "
        "Call this once at the start of a conversation before building queries."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

TOOL_DECLARATIONS = [EXECUTE_QUERY_DECLARATION, GET_QUERY_REFERENCE_DECLARATION]


# --- Tool execution ---

def run_tool(name: str, args: dict, df: pd.DataFrame, sessions: dict) -> str:
    """Execute a tool and return result as string for the LLM."""
    if name == "execute_query":
        return _run_execute_query(args, df, sessions)
    if name == "get_query_reference":
        return _get_query_reference()
    return json.dumps({"error": f"Unknown tool: {name}"})


def _normalize_query(query: dict) -> dict:
    """Fix common LLM formatting issues in query JSON."""
    # Gemini sometimes sends map values as {"expression": "..."} instead of "..."
    if "map" in query and isinstance(query["map"], dict):
        query["map"] = {
            k: v["expression"] if isinstance(v, dict) and "expression" in v else v
            for k, v in query["map"].items()
        }
    return query


def _run_execute_query(args: dict, df: pd.DataFrame, sessions: dict) -> str:
    query = _normalize_query(args.get("query", {}))
    log.info(f"Executing query: {json.dumps(query)}")

    try:
        result = execute(query, df, sessions)
    except QueryError as e:
        log.warning(f"Query error: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": e.error_type,
            "step": e.step,
            "expression": e.expression,
            "hint": "Fix the query and retry.",
        })
    except Exception as e:
        log.exception("Unexpected error executing query")
        return json.dumps({
            "error": f"Internal error: {e}",
            "hint": "Simplify the query and retry.",
        })

    return json.dumps({
        "result": result["result"],
        "metadata": result["metadata"],
        "has_table": result["table"] is not None,
        "row_count": len(result["table"]) if result["table"] else None,
    }, default=str)


def _get_query_reference() -> str:
    return _QUERY_REFERENCE


_QUERY_REFERENCE = """\
# Barb Script Query Reference

## Query Format
JSON object with these fields (all optional):
- session: Trading session filter (RTH, ETH, OVERNIGHT, ASIAN, EUROPEAN, MORNING, AFTERNOON, RTH_OPEN, RTH_CLOSE)
- from: Timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly). Default: 1m
- period: Date range ("2024", "2024-03", "2024-01-01:2024-06-30", "last_year", "last_month", "last_week")
- map: Derived columns {name: "expression_string"}. Values MUST be strings.
- where: Row filter expression (boolean)
- group_by: Column to group by
- select: Aggregate expression. Default: count()
- sort: "column_name asc" or "column_name desc"
- limit: Max rows (positive integer)

## Execution Order
session → period → from → map → where → group_by → select → sort → limit

## Expressions
Arithmetic: +, -, *, /
Comparison: >, <, >=, <=, ==, !=
Boolean: and, or, not
Membership: weekday in [0, 1, 4]
Columns: open, high, low, close, volume (plus any map-defined columns)

## Functions

Scalar: abs(x), log(x), sqrt(x), sign(x), round(x, n), if(cond, then, else)
Lag: prev(col), prev(col, n), next(col), next(col, n)
Window: rolling_mean(col, n), rolling_sum(col, n), rolling_max(col, n), rolling_min(col, n), rolling_std(col, n), rolling_count(cond, n), ema(col, n)
Cumulative: cummax(col), cummin(col), cumsum(col)
Pattern: streak(cond), bars_since(cond), rank(col)
Aggregate: mean(col), sum(col), max(col), min(col), std(col), median(col), count(), percentile(col, p), correlation(col1, col2), last(col)
Time: dayofweek(), dayname(), hour(), month(), monthname(), year(), day(), quarter(), date()

## Examples

Average daily range:
{"session": "RTH", "from": "daily", "map": {"range": "high - low"}, "select": "mean(range)"}

Bullish day count:
{"session": "RTH", "from": "daily", "where": "close > open", "select": "count()"}

Volume by weekday:
{"session": "RTH", "from": "daily", "map": {"weekday": "dayofweek()"}, "group_by": "weekday", "select": "mean(volume)", "sort": "weekday asc"}

Inside days:
{"session": "RTH", "from": "daily", "where": "high < prev(high) and low > prev(low)", "select": "count()"}

Gap analysis:
{"session": "RTH", "from": "daily", "map": {"gap": "open - prev(close)"}, "where": "gap != 0", "select": "mean(abs(gap))"}

NR7 (narrowest range of 7 days):
{"session": "RTH", "from": "daily", "map": {"range": "high - low", "min7": "rolling_min(range, 7)"}, "where": "range == min7", "select": "count()"}

Top 3 highest volume weekdays:
{"session": "RTH", "from": "daily", "map": {"weekday": "dayofweek()"}, "group_by": "weekday", "select": "mean(volume)", "sort": "mean_volume desc", "limit": 3}
"""
