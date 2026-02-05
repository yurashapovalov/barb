"""Tool definitions and execution for the LLM assistant.

Tools:
- get_query_reference: returns the Barb Script format reference
- execute_query: runs a Barb Script query against OHLCV data
"""

import json

import pandas as pd

from assistant.tools import execute, reference

__all__ = ["TOOL_DECLARATIONS", "run_tool"]

TOOL_DECLARATIONS = [
    reference.DECLARATION,
    execute.DECLARATION,
]

_HANDLERS = {
    "get_query_reference": lambda args, df, sessions: (reference.run(args), None),
    "execute_query": lambda args, df, sessions: execute.run(args, df, sessions),
}


def run_tool(name: str, args: dict, df: pd.DataFrame, sessions: dict) -> tuple[str, dict | None]:
    """Execute a tool. Returns (result_string_for_llm, raw_result_or_none)."""
    handler = _HANDLERS.get(name)
    if handler:
        return handler(args, df, sessions)
    return json.dumps({"error": f"Unknown tool: {name}"}), None
