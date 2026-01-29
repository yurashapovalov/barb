#!/usr/bin/env python3
"""End-to-end test: real Gemini API calls through the full Barb pipeline.

Usage:
    python scripts/e2e.py              # run all scenarios
    python scripts/e2e.py --scenario 1 # run single scenario (1-indexed)
    python scripts/e2e.py --quiet      # just pass/fail, no trace details
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
from config.market.instruments import get_instrument

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


# --- Test scenarios ---

SCENARIOS = [
    {
        "name": "Analytical — average daily range",
        "messages": [
            "What is the average daily range for NQ?",
        ],
        "expect_tools": ["understand_question", "execute_query"],
        "expect_data": True,
    },
    {
        "name": "Filtered — inside days in 2024",
        "messages": [
            "How many inside days were there in 2024?",
        ],
        "expect_tools": ["understand_question", "execute_query"],
        "expect_data": True,
    },
    {
        "name": "Knowledge — no query needed",
        "messages": [
            "What is NR7?",
        ],
        "expect_tools": [],
        "expect_data": False,
    },
    {
        "name": "Multi-turn — follow-up question",
        "messages": [
            "What is the average daily range for NQ?",
            "Now break it down by weekday",
        ],
        "expect_tools": ["execute_query"],
        "expect_data": True,
    },
    {
        "name": "Group-by — volume by month 2024",
        "messages": [
            "Show me average daily volume by month for 2024",
        ],
        "expect_tools": ["understand_question", "execute_query"],
        "expect_data": True,
    },
    {
        "name": "Russian — gap analysis",
        "messages": [
            "Какой средний размер гэпа на открытии NQ за последний год?",
        ],
        "expect_tools": ["understand_question", "execute_query"],
        "expect_data": True,
    },
    {
        "name": "Russian — weekday high/low distribution",
        "messages": [
            "Распредели дни недели по частоте хай лоу приходящимся на этот день в течение недели",
        ],
        "expect_tools": ["understand_question"],
        "expect_data": False,
    },
    {
        "name": "Russian — ATH by weekday",
        "messages": [
            "На какие дни недели чаще всего приходился ATH показать списком по убыванию частоты",
        ],
        "expect_tools": ["understand_question"],
        "expect_data": False,
    },
]


def create_assistant():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(f"{C.RED}ERROR: GEMINI_API_KEY not set. Add to .env or export.{C.END}")
        sys.exit(1)

    instrument = "NQ"
    config = get_instrument(instrument)
    df = load_data(instrument)
    return Assistant(
        api_key=api_key,
        instrument=instrument,
        df=df,
        sessions=config["sessions"],
    )


def print_trace(result, show_prompt=False):
    """Print tool call trace from a chat result."""
    if show_prompt:
        print(f"{C.DIM}    Model: {result.get('model', '?')}{C.END}")

    for step in result.get("steps", []):
        tool = step["tool"]
        args = step["args"]
        tool_result = step["result"]

        if tool == "get_query_reference":
            print(f"{C.CYAN}    [{step['round']}] {tool}{C.END}"
                  f"{C.DIM} → {len(tool_result)} chars{C.END}")
            continue

        if tool == "execute_query":
            query = args.get("query", {})
            print(f"{C.CYAN}    [{step['round']}] {tool}{C.END}")
            print(f"{C.DIM}    Query: {json.dumps(query)}{C.END}")

            try:
                parsed = json.loads(tool_result)
                if "error" in parsed:
                    print(f"{C.RED}    → ERROR: {parsed['error']}{C.END}")
                elif parsed.get("has_table"):
                    print(f"{C.GREEN}    → table: {parsed['row_count']} rows{C.END}")
                else:
                    print(f"{C.GREEN}    → {parsed['result']}{C.END}")
            except json.JSONDecodeError:
                print(f"{C.YELLOW}    → {tool_result[:100]}{C.END}")
            continue

        print(f"{C.CYAN}    [{step['round']}] {tool}({args}){C.END}")


def run_checks(result, scenario):
    """Run soft checks on a scenario result. Returns list of warnings."""
    warnings = []

    if not result["answer"].strip():
        warnings.append("Empty answer")

    tools_called = [s["tool"] for s in result.get("steps", [])]
    expect_tools = scenario["expect_tools"]

    if expect_tools:
        for expected in expect_tools:
            if expected not in tools_called:
                warnings.append(f"Expected tool '{expected}' not called (got: {tools_called})")
    else:
        if tools_called:
            warnings.append(f"Expected no tools, got: {tools_called}")

    data = result.get("data", [])
    if scenario.get("expect_data"):
        if not data:
            warnings.append("Expected data block but got none")
        for d in data:
            if d.get("result") is None:
                warnings.append("Data block has no result")
    else:
        if data:
            warnings.append(f"Expected no data, got {len(data)} blocks")

    return warnings


def run_scenario(assistant, scenario, quiet=False):
    """Run one scenario. Returns result dict with full log for saving."""
    name = scenario["name"]
    messages = scenario["messages"]

    print(f"\n{'='*70}")
    print(f"{C.BOLD}{C.MAGENTA}  {name}{C.END}")
    print(f"{'='*70}")

    history = []
    last_result = None
    all_warnings = []
    turns = []

    for i, msg in enumerate(messages):
        print(f"\n{C.BLUE}>>> {msg}{C.END}")

        start = time.time()
        try:
            result = assistant.chat(msg, history=history or None, trace=True)
        except Exception as e:
            print(f"{C.RED}    CRASH: {e}{C.END}")
            turns.append({"user": msg, "error": str(e)})
            return {
                "name": name, "passed": False, "cost": None,
                "turns": turns, "warnings": ["CRASH: " + str(e)],
            }

        elapsed = time.time() - start
        last_result = result

        if not quiet:
            print_trace(result, show_prompt=(i == 0))

        # Print data blocks (direct from interpreter, not from model)
        for d in result.get("data", []):
            query_str = json.dumps(d["query"])
            print(f"\n{C.BOLD}    DATA:{C.END} {d['result']}")
            print(f"{C.DIM}    Query: {query_str}{C.END}")
            if d.get("rows"):
                print(f"{C.DIM}    Rows: {d['rows']}, "
                      f"Session: {d.get('session', '-')}, "
                      f"Timeframe: {d.get('timeframe', '-')}{C.END}")

        # Print model commentary
        answer = result["answer"]
        if len(answer) > 500:
            answer = answer[:500] + "..."
        print(f"\n{C.GREEN}<<< {answer}{C.END}")

        # Cost and timing
        cost = result["cost"]
        print(f"{C.DIM}    ${cost['total_cost']:.6f} "
              f"({cost['input_tokens']}in/{cost['output_tokens']}out) "
              f"{elapsed:.1f}s{C.END}")

        # Run checks on last message
        if i == len(messages) - 1:
            all_warnings = run_checks(result, scenario)

        # Save turn for log
        turns.append({
            "user": msg,
            "answer": result["answer"],
            "steps": result.get("steps", []),
            "cost": result["cost"],
            "model": result.get("model"),
            "elapsed_s": round(elapsed, 2),
        })

        # Accumulate history
        history.append({"role": "user", "text": msg})
        history.append({"role": "model", "text": result["answer"]})

    # Print status
    if all_warnings:
        for w in all_warnings:
            print(f"{C.YELLOW}    WARN: {w}{C.END}")
        print(f"\n    {C.YELLOW}WARN{C.END}")
    else:
        print(f"\n    {C.GREEN}PASS{C.END}")

    return {
        "name": name,
        "passed": len(all_warnings) == 0,
        "cost": last_result["cost"] if last_result else None,
        "turns": turns,
        "warnings": all_warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Barb end-to-end test")
    parser.add_argument("--scenario", type=int, help="Run single scenario (1-indexed)")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    print(f"{C.BOLD}Loading data...{C.END}")
    assistant = create_assistant()
    print(f"{C.DIM}Ready.{C.END}")

    scenarios = SCENARIOS
    if args.scenario:
        idx = args.scenario - 1
        if 0 <= idx < len(SCENARIOS):
            scenarios = [SCENARIOS[idx]]
        else:
            print(f"Invalid scenario. Valid: 1-{len(SCENARIOS)}")
            sys.exit(1)

    results = []
    for scenario in scenarios:
        r = run_scenario(assistant, scenario, quiet=args.quiet)
        results.append(r)

    # Summary
    print(f"\n{'='*70}")
    print(f"{C.BOLD}  SUMMARY{C.END}")
    print(f"{'='*70}\n")

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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": datetime.now().isoformat(),
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

    path = results_dir / f"{timestamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    print(f"\n  Saved: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
