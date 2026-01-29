"""execute_query tool — run Barb Script queries against OHLCV data."""

import json
import logging

import pandas as pd

from barb.interpreter import execute, QueryError

log = logging.getLogger(__name__)


DECLARATION = {
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


def run(args: dict, df: pd.DataFrame, sessions: dict) -> str:
    """Execute a Barb Script query and return result as JSON string."""
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


def _normalize_query(query: dict) -> dict:
    """Fix common LLM formatting issues in query JSON."""
    # Gemini sometimes sends map values as {"expression": "..."} instead of "..."
    if "map" in query and isinstance(query["map"], dict):
        query["map"] = {
            k: v["expression"] if isinstance(v, dict) and "expression" in v else v
            for k, v in query["map"].items()
        }
    return query
