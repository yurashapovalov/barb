"""understand_question tool — engine capabilities check before query execution."""

import json


DECLARATION = {
    "name": "understand_question",
    "description": (
        "Analyze a user question before executing queries. "
        "Returns engine capabilities and limitations so you can explain "
        "what you will compute or honestly say what is not possible. "
        "Call this before execute_query."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The user's question to analyze",
            },
        },
        "required": ["question"],
    },
}


def run(args: dict) -> str:
    """Return engine capabilities and limitations."""
    return json.dumps({
        "capabilities": {
            "single_timeframe": "1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly",
            "sessions": "RTH, ETH, OVERNIGHT, ASIAN, EUROPEAN, MORNING, AFTERNOON",
            "computed_columns": "arithmetic, comparisons, if(cond, then, else), lag (prev/next), rolling windows, cumulative, patterns",
            "filtering": "boolean expressions on any column",
            "grouping": "by any column (weekday, month, year, etc.)",
            "aggregation": "mean, sum, count, min, max, std, median, percentile, correlation, last",
            "time_functions": "dayofweek, dayname, hour, month, monthname, year, quarter, date",
            "pipeline": "session -> period -> timeframe -> map -> where -> group_by -> select -> sort -> limit",
        },
        "limitations": [
            "Cross-timeframe queries not supported (e.g. comparing daily values with weekly aggregates in one query)",
            "No subqueries or nested queries",
            "No JOINs or multiple data sources",
            "No loops or arbitrary code",
        ],
        "instructions": (
            "Explain to the user what you understood and what you will compute. "
            "If the question requires unsupported capabilities, say so honestly "
            "and suggest 1-2 closest alternatives that ARE supported. "
            "Never silently substitute a different question."
        ),
    })
