#!/usr/bin/env python3
"""End-to-end test: real Anthropic API calls through the full Barb pipeline.

Usage:
    python scripts/e2e.py                          # run all scenarios
    python scripts/e2e.py --scenario 1             # run single scenario (1-indexed)
    python scripts/e2e.py --scenario "session high" # run by name substring
    python scripts/e2e.py --quiet                  # just pass/fail, no trace details
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Load .env
_env_file = ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from assistant.chat import Assistant
from barb.data import load_data
from config.market.instruments import get_instrument, register_instrument
from scripts.e2e_scenarios import SCENARIOS
from supabase import create_client

# --- ANSI colors ---


class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    END = "\033[0m"


_instruments_loaded = False


def _load_instruments():
    """Load instruments from Supabase (same as api/main.py lifespan). Runs once."""
    global _instruments_loaded
    if _instruments_loaded:
        return
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print(f"{C.RED}ERROR: SUPABASE_URL/SUPABASE_SERVICE_KEY not set.{C.END}")
        sys.exit(1)
    db = create_client(url, key)
    result = db.table("instrument_full").select("*").execute()
    for row in result.data:
        register_instrument(row)
    print(f"{C.DIM}Loaded {len(result.data)} instruments from Supabase{C.END}")
    _instruments_loaded = True


# Cache assistants by (instrument, model) to avoid recreating for same instrument
_assistant_cache: dict[tuple[str, str | None], Assistant] = {}


def get_assistant(instrument: str, model=None) -> Assistant:
    """Get or create an Assistant for the given instrument."""
    cache_key = (instrument, model)
    if cache_key in _assistant_cache:
        return _assistant_cache[cache_key]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(f"{C.RED}ERROR: ANTHROPIC_API_KEY not set. Add to .env or export.{C.END}")
        sys.exit(1)

    _load_instruments()

    config = get_instrument(instrument)
    if not config:
        print(f"{C.RED}ERROR: Instrument {instrument} not found in Supabase{C.END}")
        sys.exit(1)

    assistant = Assistant(
        api_key=api_key,
        instrument=instrument,
        df_daily=load_data(instrument, "1d"),
        df_minute=load_data(instrument, "1m"),
        sessions=config["sessions"],
        model=model,
    )
    _assistant_cache[cache_key] = assistant
    return assistant


def chat_sync(assistant, message, history=None):
    """Consume chat_stream into a single result dict."""
    steps = []
    data = []
    answer = ""
    cost = None
    current_tool = None

    for event in assistant.chat_stream(message, history=history, auto_execute=True):
        etype = event["event"]

        if etype == "tool_start":
            current_tool = {
                "tool": event["data"]["tool_name"],
                "args": event["data"]["input"],
                "round": len(steps) + 1,
            }

        elif etype == "tool_end":
            if current_tool:
                current_tool["result"] = ""
                current_tool["duration_ms"] = event["data"]["duration_ms"]
                current_tool["error"] = event["data"]["error"]
                steps.append(current_tool)
                current_tool = None

        elif etype == "data_block":
            data.append(event["data"])

        elif etype == "text_delta":
            answer += event["data"]["delta"]

        elif etype == "done":
            d = event["data"]
            answer = d["answer"]
            cost = d["usage"]
            data = d["data"]
            # Enrich steps with tool results from done event
            for i, tc in enumerate(d.get("tool_calls", [])):
                if i < len(steps):
                    steps[i]["result"] = tc.get("output", "")

    return {
        "answer": answer,
        "steps": steps,
        "data": data,
        "cost": cost,
    }


def print_trace(result, show_prompt=False):
    """Print tool call trace from a chat result."""
    for step in result.get("steps", []):
        tool = step["tool"]
        args = step["args"]
        tool_result = step.get("result", "")

        # Format query args nicely
        if "query" in args:
            args_str = json.dumps(args["query"], ensure_ascii=False)
            if len(args_str) > 80:
                args_str = args_str[:77] + "..."
        else:
            args_str = ", ".join(f"{k}={v!r}" for k, v in args.items()) if args else ""

        prefix = f"{C.CYAN}    [{step['round']}] {tool}({args_str}){C.END}"

        if step.get("error"):
            print(f"{prefix} {C.RED}→ ERROR: {step['error']}{C.END}")
        elif tool_result and len(tool_result) > 100:
            print(f"{prefix} {C.DIM}→ {tool_result[:80]}...{C.END}")
        elif tool_result:
            print(f"{prefix} {C.GREEN}→ {tool_result}{C.END}")
        else:
            print(prefix)


def run_checks(turns, scenario):
    """Run soft checks across all turns. Returns list of warnings."""
    warnings = []

    last_answer = turns[-1].get("answer", "") if turns else ""
    if not last_answer.strip():
        warnings.append("Empty answer")

    # Check if tool was called when expected
    all_tools = []
    for turn in turns:
        for step in turn.get("steps", []):
            all_tools.append(step["tool"])

    expect_tool = scenario.get("expect_tool", False)
    if expect_tool and not all_tools:
        warnings.append("Expected tool call but got none")
    elif not expect_tool and all_tools:
        warnings.append(f"Expected no tools, got: {all_tools}")

    return warnings


def run_scenario(assistant, scenario, quiet=False):
    """Run one scenario. Returns result dict with full log for saving."""
    name = scenario["name"]
    messages = scenario["messages"]

    print(f"\n{'=' * 70}")
    print(f"{C.BOLD}{C.MAGENTA}  {name}{C.END}")
    print(f"{'=' * 70}")

    history = []
    last_result = None
    all_warnings = []
    turns = []

    for i, msg in enumerate(messages):
        print(f"\n{C.BLUE}>>> {msg}{C.END}")

        start = time.time()
        try:
            result = chat_sync(assistant, msg, history=history or None)
        except Exception as e:
            print(f"{C.RED}    CRASH: {e}{C.END}")
            turns.append({"user": msg, "error": str(e)})
            return {
                "name": name,
                "passed": False,
                "cost": None,
                "turns": turns,
                "warnings": ["CRASH: " + str(e)],
            }

        elapsed = time.time() - start
        last_result = result

        if not quiet:
            print_trace(result, show_prompt=(i == 0))

        # Print data blocks
        for d in result.get("data", []):
            tool_name = d.get("tool", "?")
            rows = d.get("rows")
            result_preview = str(d.get("result", ""))[:200]
            print(f"\n{C.BOLD}    DATA ({tool_name}):{C.END} {result_preview}")
            if rows:
                print(f"{C.DIM}    Rows: {rows}{C.END}")

        # Print model commentary
        answer = result["answer"]
        if len(answer) > 500:
            answer = answer[:500] + "..."
        print(f"\n{C.GREEN}<<< {answer}{C.END}")

        # Cost and timing
        cost = result["cost"]
        cache_read = cost.get("cache_read_tokens", 0)
        cache_write = cost.get("cache_write_tokens", 0)
        extras = ""
        if cache_read:
            extras += f" cache_read:{cache_read}"
        if cache_write:
            extras += f" cache_write:{cache_write}"
        print(
            f"{C.DIM}    ${cost['total_cost']:.6f} "
            f"({cost['input_tokens']}in/{cost['output_tokens']}out{extras}) "
            f"{elapsed:.1f}s{C.END}"
        )

        # Run checks after last message
        if i == len(messages) - 1:
            all_warnings = run_checks(
                turns + [{"answer": result["answer"], "steps": result.get("steps", [])}], scenario
            )
            # Check data across all turns
            all_data = []
            for t in turns:
                all_data.extend(t.get("data", []))
            all_data.extend(result.get("data", []))
            if scenario.get("expect_data"):
                if not all_data:
                    all_warnings.append("Expected data block but got none")
            else:
                if all_data:
                    all_warnings.append(f"Expected no data, got {len(all_data)} blocks")

        # Save turn for log
        turns.append(
            {
                "user": msg,
                "answer": result["answer"],
                "steps": result.get("steps", []),
                "data": result.get("data", []),
                "cost": result["cost"],
                "elapsed_s": round(elapsed, 2),
            }
        )

        # Accumulate history with tool calls for model context
        history.append({"role": "user", "text": msg})
        entry = {"role": "assistant", "text": result["answer"]}
        tool_calls = [
            {"tool_name": s["tool"], "input": s["args"], "output": s["result"]}
            for s in result.get("steps", [])
        ]
        if tool_calls:
            entry["tool_calls"] = tool_calls
        history.append(entry)

    # Print status
    if all_warnings:
        for w in all_warnings:
            print(f"{C.YELLOW}    WARN: {w}{C.END}")
        print(f"\n    {C.YELLOW}WARN{C.END}")
    else:
        print(f"\n    {C.GREEN}PASS{C.END}")

    # Sum cost across all turns
    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "input_cost": 0.0,
        "output_cost": 0.0,
        "total_cost": 0.0,
    }
    for t in turns:
        if t.get("cost"):
            for k in total_cost:
                total_cost[k] += t["cost"].get(k, 0)

    return {
        "name": name,
        "passed": len(all_warnings) == 0,
        "cost": total_cost,
        "turns": turns,
        "warnings": all_warnings,
    }


def _select_scenarios(selector: str | None) -> list[dict]:
    """Select scenarios by 1-indexed number or name substring."""
    if not selector:
        return SCENARIOS

    # Try as number first
    try:
        idx = int(selector) - 1
        if 0 <= idx < len(SCENARIOS):
            return [SCENARIOS[idx]]
        print(f"Invalid scenario index. Valid: 1-{len(SCENARIOS)}")
        sys.exit(1)
    except ValueError:
        pass

    # Match by name substring (case-insensitive)
    needle = selector.lower()
    matched = [s for s in SCENARIOS if needle in s["name"].lower()]
    if not matched:
        print(f"No scenarios matching '{selector}'. Available:")
        for i, s in enumerate(SCENARIOS, 1):
            print(f"  {i}. {s['name']}")
        sys.exit(1)
    return matched


def main():
    parser = argparse.ArgumentParser(description="Barb end-to-end test")
    parser.add_argument(
        "--scenario", type=str, help="Scenario number (1-indexed) or name substring"
    )
    parser.add_argument("--model", type=str, help="Override model (e.g. claude-haiku-4-5-20251001)")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    scenarios = _select_scenarios(args.scenario)

    print(f"{C.BOLD}Loading data...{C.END}")

    # Pre-load assistants for all instruments needed
    instruments = {s.get("instrument", "NQ") for s in scenarios}
    for instrument in sorted(instruments):
        assistant = get_assistant(instrument, model=args.model)
        print(f"{C.DIM}Ready: {instrument} | Model: {assistant.model}{C.END}")

    results = []
    for scenario in scenarios:
        instrument = scenario.get("instrument", "NQ")
        assistant = get_assistant(instrument, model=args.model)
        r = run_scenario(assistant, scenario, quiet=args.quiet)
        results.append(r)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"{C.BOLD}  SUMMARY{C.END}")
    print(f"{'=' * 70}\n")

    total_cost = 0.0
    passed = 0
    for r in results:
        cost = r["cost"]["total_cost"] if r["cost"] else 0
        total_cost += cost
        if r["passed"]:
            passed += 1
            status = f"{C.GREEN}PASS{C.END}"
        else:
            status = f"{C.YELLOW}WARN{C.END}"
        print(f"  {status}  {r['name']}  {C.DIM}${cost:.6f}{C.END}")

    print(f"\n  {passed}/{len(results)} passed | Total: ${total_cost:.6f}")

    # Save results
    results_dir = ROOT / "results" / "e2e"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Use model from first assistant
    first_instrument = scenarios[0].get("instrument", "NQ")
    model_name = get_assistant(first_instrument, model=args.model).model

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "passed": passed,
        "total": len(results),
        "total_cost": total_cost,
        "scenarios": [
            {
                "name": r["name"],
                "passed": r["passed"],
                "warnings": r.get("warnings", []),
                "cost": r["cost"],
                "turns": r.get("turns", []),
            }
            for r in results
        ],
    }

    model_short = model_name.split("-")[1] if "-" in model_name else model_name
    path = results_dir / f"{timestamp}_{model_short}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    print(f"\n  Saved: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
