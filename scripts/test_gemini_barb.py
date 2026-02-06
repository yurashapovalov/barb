"""Test: Gemini Flash with single Barb Script tool (JSON query)."""

import json
import os
import sys
from pathlib import Path

# Load .env
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
_env_file = ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from google import genai
from google.genai import types

from barb.data import load_data
from barb.interpreter import execute, QueryError
from config.market.instruments import get_instrument

# Scenario: Inside Day
TURNS = [
    "сколько inside days было за 2024-2025?",
    "да, RTH",
    "какой средний range на следующий день после inside day?",
    "покажи топ-10 самых сильных движений после inside day",
]

BARB_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="run_query",
            description="""Execute a Barb Script query against market data.

Query is a flat JSON with these fields (all optional):
- session: "RTH" or "ETH" — filter by trading session
- from: "1m", "5m", "15m", "30m", "1h", "daily", "weekly" — timeframe
- period: "2024", "2024-03", "2024-01:2024-06", "last_year" — date filter
- map: {"col_name": "expression"} — compute derived columns
- where: "expression" — filter rows (boolean)
- group_by: "column" or ["col1", "col2"] — group rows
- select: "mean(col)" or ["sum(x)", "count()"] — aggregate
- sort: "column desc" or "column asc"
- limit: number — max rows

Execution order is FIXED: session → period → from → map → where → group_by → select → sort → limit

Examples:
1. Count inside days:
   {"session": "RTH", "from": "daily", "period": "2024:2025", "map": {"inside_day": "high < prev(high) and low > prev(low)"}, "where": "inside_day", "select": "count()"}

2. Average range after inside day:
   {"session": "RTH", "from": "daily", "period": "2024:2025", "map": {"inside_day": "high < prev(high) and low > prev(low)", "next_range": "next(high - low)"}, "where": "inside_day", "select": "mean(next_range)"}

3. Top 10 movements (table):
   {"session": "RTH", "from": "daily", "period": "2024:2025", "map": {"inside_day": "high < prev(high) and low > prev(low)", "next_range": "next(high - low)"}, "where": "inside_day", "sort": "next_range desc", "limit": 10}
""",
            parameters=types.Schema(
                type="object",
                properties={
                    "query": types.Schema(
                        type="object",
                        description="Barb Script query object",
                    ),
                },
                required=["query"],
            ),
        )
    ]
)


def run_barb_query(query: dict, df, sessions) -> str:
    """Execute query and return result as string."""
    try:
        result = execute(query, df, sessions)
        if result.get("table"):
            rows = result["table"][:20]
            return f"Result: {len(result['table'])} rows\n{json.dumps(rows, indent=2, default=str)}"
        else:
            return f"Result: {result['result']}"
    except QueryError as e:
        return f"Error: {e}"


def run_test():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        return
    client = genai.Client(api_key=api_key)

    # Load data
    instrument = "NQ"
    df = load_data(instrument)
    config = get_instrument(instrument)
    sessions = config["sessions"]

    system_prompt = f"""You are Barb — a trading data analyst for NQ (Nasdaq 100 E-mini).

You have ONE tool: run_query. It executes Barb Script queries against OHLCV data.
Data: 2006 to present, 1-minute bars.
Sessions: RTH (09:30-17:00), ETH (18:00-09:30).

IMPORTANT:
- Build ONE query per question. The query handles everything.
- map computes columns BEFORE where filters. Order is fixed.
- For "next day" stats, use next() function: next(high - low) gives tomorrow's range.
- prev() gives previous row value.
- Always include the period from the conversation context.

Answer in Russian. Keep responses short (1-2 sentences about what the result means)."""

    history = []

    print("=" * 60)
    print("Testing Gemini Flash with Barb Script (single JSON query)")
    print("=" * 60)

    for turn_num, user_msg in enumerate(TURNS, 1):
        print(f"\n--- Turn {turn_num} ---")
        print(f"User: {user_msg}")

        history.append(types.Content(role="user", parts=[types.Part(text=user_msg)]))

        for round_num in range(3):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[BARB_TOOL],
                    temperature=0,
                ),
            )

            # Check for tool calls
            tool_calls = []
            text_response = ""

            for part in response.candidates[0].content.parts:
                if part.function_call:
                    tool_calls.append(part.function_call)
                    query = dict(part.function_call.args.get("query", {}))
                    print(f"  Query: {json.dumps(query, ensure_ascii=False)}")
                elif part.text:
                    text_response += part.text

            history.append(response.candidates[0].content)

            if not tool_calls:
                print(f"Assistant: {text_response[:300]}...")
                break

            # Execute tools
            tool_results = []
            for fc in tool_calls:
                query = dict(fc.args.get("query", {}))
                result = run_barb_query(query, df, sessions)
                print(f"    → {result[:150]}...")
                tool_results.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"result": result},
                        )
                    )
                )

            history.append(types.Content(role="user", parts=tool_results))

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)


if __name__ == "__main__":
    run_test()
