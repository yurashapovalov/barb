"""Test: Hard scenario — gap fill analysis with follow-ups."""

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

import anthropic
from google import genai
from google.genai import types

from barb.data import load_data
from barb.interpreter import execute, QueryError
from config.market.instruments import get_instrument

# Hard scenario: Gap fill analysis
TURNS = [
    "какой процент гэпов вверх больше 50 пунктов закрывается в тот же день? (2024)",
    "а гэпов вниз?",
    "в какой день недели лучше всего закрываются гэпы?",
    "покажи 5 самых больших незакрытых гэпов вверх",
]

BARB_TOOL_SCHEMA = {
    "name": "run_query",
    "description": """Execute a Barb Script query against market data.

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

Key expressions:
- prev(col) — previous row value
- next(col) — next row value
- dayname() — day of week name (Mon, Tue, etc)
- abs(x) — absolute value

Gap fill logic:
- Gap up: open > prev(close) — today opened higher than yesterday's close
- Gap filled: low <= prev(close) — today's low touched yesterday's close
- Gap size: open - prev(close)
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "object",
                "description": "Barb Script query object",
            },
        },
        "required": ["query"],
    },
}


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


def test_sonnet(df, sessions):
    """Test with Claude Sonnet."""
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )

    system_prompt = """You are Barb — a trading data analyst for NQ (Nasdaq 100 E-mini).

You have ONE tool: run_query. It executes Barb Script queries against OHLCV data.
Data: 2006 to present, 1-minute bars. Sessions: RTH (09:30-17:00), ETH (18:00-09:30).

CRITICAL:
- Always include session: "RTH" for daily data.
- To compute percentage: run TWO queries — one for total count, one for filtered count. Then calculate %.
- Gap up = open > prev(close). Gap filled = low <= prev(close).
- group_by requires a COLUMN NAME, not an expression. Create column in map first: {"dow": "dayname()"}, then group_by: "dow".
- select only supports simple aggregates: count(), sum(col), mean(col), min(col), max(col). No SQL syntax.
- Always keep the period from conversation context.

Answer in Russian. Keep responses short."""

    messages = []
    print("\n" + "=" * 60)
    print("HAIKU 4.5 + Barb Script")
    print("=" * 60)

    for turn_num, user_msg in enumerate(TURNS, 1):
        print(f"\n--- Turn {turn_num} ---")
        print(f"User: {user_msg}")
        messages.append({"role": "user", "content": user_msg})

        for _ in range(5):
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=system_prompt,
                tools=[BARB_TOOL_SCHEMA],
                messages=messages,
            )

            assistant_content = []
            tool_calls = []
            text_response = ""

            for block in response.content:
                if block.type == "text":
                    text_response += block.text
                    assistant_content.append(block)
                elif block.type == "tool_use":
                    tool_calls.append(block)
                    assistant_content.append(block)
                    print(f"  Query: {json.dumps(block.input.get('query', {}), ensure_ascii=False)}")

            messages.append({"role": "assistant", "content": assistant_content})

            if not tool_calls:
                print(f"Assistant: {text_response[:400]}...")
                break

            tool_results = []
            for tool_call in tool_calls:
                query = tool_call.input.get("query", {})
                result = run_barb_query(query, df, sessions)
                print(f"    → {result[:100]}...")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result,
                })
            messages.append({"role": "user", "content": tool_results})


def test_gemini(df, sessions):
    """Test with Gemini Flash."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set, skipping")
        return

    client = genai.Client(api_key=api_key)

    gemini_tool = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="run_query",
                description=BARB_TOOL_SCHEMA["description"],
                parameters=types.Schema(
                    type="object",
                    properties={
                        "query": types.Schema(type="object", description="Barb Script query"),
                    },
                    required=["query"],
                ),
            )
        ]
    )

    system_prompt = """You are Barb — a trading data analyst for NQ (Nasdaq 100 E-mini).

You have ONE tool: run_query. It executes Barb Script queries against OHLCV data.
Data: 2006 to present, 1-minute bars. Sessions: RTH (09:30-17:00), ETH (18:00-09:30).

CRITICAL:
- To compute percentage: run TWO queries — one for total count, one for filtered count. Then calculate %.
- Gap up = open > prev(close). Gap filled = low <= prev(close).
- For group stats: use group_by + select with aggregate function.
- Always keep the period from conversation context.

Answer in Russian. Keep responses short."""

    history = []
    print("\n" + "=" * 60)
    print("GEMINI + Barb Script")
    print("=" * 60)

    for turn_num, user_msg in enumerate(TURNS, 1):
        print(f"\n--- Turn {turn_num} ---")
        print(f"User: {user_msg}")
        history.append(types.Content(role="user", parts=[types.Part(text=user_msg)]))

        for _ in range(5):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[gemini_tool],
                    temperature=0,
                ),
            )

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
                print(f"Assistant: {text_response[:400]}...")
                break

            tool_results = []
            for fc in tool_calls:
                query = dict(fc.args.get("query", {}))
                result = run_barb_query(query, df, sessions)
                print(f"    → {result[:100]}...")
                tool_results.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"result": result},
                        )
                    )
                )
            history.append(types.Content(role="user", parts=tool_results))


def main():
    instrument = "NQ"
    df = load_data(instrument)
    config = get_instrument(instrument)
    sessions = config["sessions"]

    print("Hard scenario: Gap fill analysis")
    print("Questions:")
    for i, q in enumerate(TURNS, 1):
        print(f"  {i}. {q}")

    test_sonnet(df, sessions)
    # test_gemini(df, sessions)

    print("\n" + "=" * 60)
    print("Done")
    print("=" * 60)


if __name__ == "__main__":
    main()
