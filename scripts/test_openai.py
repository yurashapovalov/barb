"""Quick test: same Barb prompt + tool with OpenAI models.

Usage:
    OPENAI_API_KEY=sk-... .venv/bin/python scripts/test_openai.py
    OPENAI_API_KEY=sk-... .venv/bin/python scripts/test_openai.py --model gpt-4.1-mini
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

from assistant.prompt import build_system_prompt
from assistant.tools import BARB_TOOL, run_query
from barb.data import load_data
from config.market.instruments import get_instrument, register_instrument
from supabase import create_client

INSTRUMENT = "CL"
MODEL = "gpt-4.1-mini"
MESSAGE = "собери за 2024-2025 год все дни когда котировки понизились на 2.5% и более"
MAX_ROUNDS = 5


def _load_instruments():
    """Load instruments from Supabase."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL/SUPABASE_SERVICE_KEY not set in .env")
        sys.exit(1)
    db = create_client(url, key)
    result = db.table("instrument_full").select("*").execute()
    for row in result.data:
        register_instrument(row)


def convert_tool(barb_tool: dict) -> dict:
    """Convert Anthropic tool format to OpenAI function calling format."""
    return {
        "type": "function",
        "function": {
            "name": barb_tool["name"],
            "description": barb_tool["description"],
            "parameters": barb_tool["input_schema"],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--message", default=MESSAGE)
    parser.add_argument("--instrument", default=INSTRUMENT)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY environment variable")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Load instruments + data
    _load_instruments()
    config = get_instrument(args.instrument)
    if not config:
        print(f"ERROR: Instrument {args.instrument} not found")
        sys.exit(1)
    sessions = config.get("sessions", {})
    df_daily = load_data(args.instrument, "1d")
    df_minute = load_data(args.instrument, "1m")

    # Build prompt
    system_prompt = build_system_prompt(args.instrument)
    openai_tool = convert_tool(BARB_TOOL)

    print(f"Model: {args.model}")
    print(f"Instrument: {args.instrument}")
    print(f"Message: {args.message}")
    print("=" * 60)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": args.message},
    ]

    total_input = 0
    total_output = 0
    rounds = []

    for round_num in range(1, MAX_ROUNDS + 1):
        round_data = {"round": round_num, "text": None, "tool_calls": []}
        start = time.time()
        create_kwargs = {
            "model": args.model,
            "messages": messages,
            "tools": [openai_tool],
        }
        # GPT-5 doesn't support temperature=0
        if "gpt-5" not in args.model:
            create_kwargs["temperature"] = 0
        response = client.chat.completions.create(**create_kwargs)
        elapsed = time.time() - start
        round_data["elapsed_s"] = round(elapsed, 1)

        usage = response.usage
        total_input += usage.prompt_tokens
        total_output += usage.completion_tokens

        msg = response.choices[0].message

        # Print text if any
        if msg.content:
            print(f"\n[Round {round_num}] Text ({elapsed:.1f}s):")
            print(msg.content)
            round_data["text"] = msg.content

        # No tool calls — done
        if not msg.tool_calls:
            rounds.append(round_data)
            break

        # Process tool calls
        messages.append(msg)

        for tc in msg.tool_calls:
            fn = tc.function
            input_data = json.loads(fn.arguments)
            query = input_data.get("query", {})
            title = input_data.get("title", "")

            print(f"\n[Round {round_num}] Tool: {fn.name} (title={title})")
            print(f"  Query: {json.dumps(query, ensure_ascii=False, indent=2)}")

            # Pick correct dataframe based on timeframe
            step0 = query["steps"][0] if query.get("steps") else query
            tf = step0.get("from", "daily")
            df = df_minute if tf in ("1m", "5m", "15m", "30m", "1h") else df_daily

            # Execute
            result = run_query(query, df, sessions)
            model_response = result.get("model_response", "")
            print(f"  Result: {model_response[:200]}")

            round_data["tool_calls"].append(
                {
                    "title": title,
                    "query": query,
                    "result": model_response,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": model_response,
                }
            )

        rounds.append(round_data)

    # Cost estimate
    if "nano" in args.model:
        cost = total_input * 0.1 / 1_000_000 + total_output * 0.4 / 1_000_000
    elif "mini" in args.model:
        cost = total_input * 0.4 / 1_000_000 + total_output * 1.6 / 1_000_000
    elif "4.1" in args.model or "4o" in args.model:
        cost = total_input * 2.0 / 1_000_000 + total_output * 8.0 / 1_000_000
    else:
        cost = 0

    print("\n" + "=" * 60)
    print(f"Tokens: {total_input} in / {total_output} out")
    if cost:
        print(f"Estimated cost: ${cost:.4f}")

    # Save JSON
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "openai")
    os.makedirs(out_dir, exist_ok=True)
    model_short = args.model.split("-2025")[0]  # gpt-4.1-mini-2025-04-14 → gpt-4.1-mini
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"{ts}_{model_short}.json")

    report = {
        "model": args.model,
        "instrument": args.instrument,
        "message": args.message,
        "rounds": rounds,
        "tokens": {"input": total_input, "output": total_output},
        "cost": round(cost, 6) if cost else None,
        "timestamp": ts,
    }
    with open(out_path, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
