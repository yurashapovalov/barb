"""Tool definitions and execution for the LLM assistant.

Tools:
- understand_question: returns engine capabilities/limitations before query execution
- get_query_reference: returns the Barb Script format reference
- execute_query: runs a Barb Script query against OHLCV data
"""

import json

import pandas as pd

from assistant.tools import understand, reference, execute

TOOL_DECLARATIONS = [
    understand.DECLARATION,
    reference.DECLARATION,
    execute.DECLARATION,
]

_HANDLERS = {
    "understand_question": lambda args, df, sessions: understand.run(args),
    "get_query_reference": lambda args, df, sessions: reference.run(args),
    "execute_query": lambda args, df, sessions: execute.run(args, df, sessions),
}


def run_tool(name: str, args: dict, df: pd.DataFrame, sessions: dict) -> str:
    """Execute a tool and return result as string for the LLM."""
    handler = _HANDLERS.get(name)
    if handler:
        return handler(args, df, sessions)
    return json.dumps({"error": f"Unknown tool: {name}"})
