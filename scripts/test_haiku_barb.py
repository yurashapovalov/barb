"""Test: Haiku with single Barb Script tool (JSON query)."""

import json

import anthropic
from assistant.prompt import build_system_prompt
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

BARB_TOOL = {
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

Examples:
1. Count inside days:
   {"session": "RTH", "from": "daily", "period": "2024:2025", "map": {"inside_day": "high < prev(high) and low > prev(low)"}, "where": "inside_day", "select": "count()"}

2. Average range after inside day:
   {"session": "RTH", "from": "daily", "period": "2024:2025", "map": {"inside_day": "high < prev(high) and low > prev(low)", "next_range": "next(high - low)"}, "where": "inside_day", "select": "mean(next_range)"}

3. Top 10 movements (table):
   {"session": "RTH", "from": "daily", "period": "2024:2025", "map": {"inside_day": "high < prev(high) and low > prev(low)", "next_range": "next(high - low)"}, "where": "inside_day", "sort": "next_range desc", "limit": 10}
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
        # Format result for the model
        if result.get("table"):
            rows = result["table"][:20]  # limit display
            return f"Result: {len(result['table'])} rows\n{json.dumps(rows, indent=2, default=str)}"
        else:
            return f"Result: {result['result']}"
    except QueryError as e:
        return f"Error: {e}"


def run_test():
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )

    # Load data
    instrument = "NQ"
    df = load_data(instrument)
    config = get_instrument(instrument)
    sessions = config["sessions"]

    # Simplified system prompt for Barb Script
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

    messages = []

    print("=" * 60)
    print("Testing Claude Haiku with Barb Script (single JSON query)")
    print("=" * 60)

    for turn_num, user_msg in enumerate(TURNS, 1):
        print(f"\n--- Turn {turn_num} ---")
        print(f"User: {user_msg}")

        messages.append({"role": "user", "content": user_msg})

        # May need multiple rounds for tool use
        for round_num in range(3):
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                system=system_prompt,
                tools=[BARB_TOOL],
                messages=messages,
            )

            # Process response
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
                print(f"Assistant: {text_response[:300]}...")
                break

            # Execute query
            tool_results = []
            for tool_call in tool_calls:
                query = tool_call.input.get("query", {})
                result = run_barb_query(query, df, sessions)
                print(f"    → {result[:150]}...")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)


if __name__ == "__main__":
    run_test()
