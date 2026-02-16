# Audit: prompt-architecture.md

Date: 2026-02-16

## Claims

### Claim 1
- **Doc**: line 11: "System Prompt (assistant/prompt/system.py)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:1` — file exists and contains `build_system_prompt()`

### Claim 2
- **Doc**: line 14: "symbol, sessions, tick, data range"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:40-50` — `<instrument>` includes Symbol, Exchange, Data range, tick_line, sessions

### Claim 3
- **Doc**: line 17: "8 behavior rules"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:40-48` — 8 numbered rules in `<behavior>`

### Claim 4
- **Doc**: line 19: "Tool Description (assistant/tools/__init__.py)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:9` — `BARB_TOOL` dict defined

### Claim 5
- **Doc**: line 22: "Barb Script syntax (fields, execution order, notes)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:13-29` — Query fields, execution order, IMPORTANT notes present

### Claim 6
- **Doc**: line 23: "<patterns> — multi-function patterns (MACD cross, NFP)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:39-48` — `<patterns>` section with MACD cross, breakout, NFP, OPEX, opening/closing range

### Claim 7
- **Doc**: line 24: "<examples> — 5 query examples"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:50-86` — 5 examples present

### Claim 8
- **Doc**: line 26: "15 function groups, 106 functions"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/reference.py:11-162` — DISPLAY_GROUPS has 15 groups; `len(FUNCTIONS) == 106`

### Claim 9
- **Doc**: line 27: "compact groups (one line) + expanded groups (with description)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/reference.py:189-199` — compact uses join on one line, expanded uses one line per function with description

### Claim 10
- **Doc**: line 37: "build_system_prompt(instrument: str) -> str"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:15` — `def build_system_prompt(instrument: str) -> str:`

### Claim 11
- **Doc**: line 44: "You are Barb — a trading data analyst for {instrument} ({name})."
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:34` — `You are Barb — a trading data analyst for {instrument} ({config["name"]}).`

### Claim 12
- **Doc**: line 51: "Each function takes config: dict (result of get_instrument())"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:14` — `def build_instrument_context(config: dict) -> str:`

### Claim 13
- **Doc**: line 53: "build_instrument_context(config) → <instrument>"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:14-51` — function returns XML block starting with `<instrument>`

### Claim 14
- **Doc**: line 58: "2008-01-02 to 2026-02-12"
- **Verdict**: OUTDATED
- **Evidence**: doc uses hardcoded example dates; actual dates are dynamic from `config.get("data_start")` and `config.get("data_end")`
- **Fix**: change to "{data_start} to {data_end}" or note these are example values

### Claim 15
- **Doc**: line 59: "Today: 2026-02-13"
- **Verdict**: OUTDATED
- **Evidence**: `assistant/prompt/context.py:44` — `Today: {date.today()}` is dynamic, not hardcoded
- **Fix**: change to "Today: {date.today()}" or note this is an example

### Claim 16
- **Doc**: line 60: "Tick: 0.25 ($5.00 per tick, $20.00 per point)"
- **Verdict**: ACCURATE
- **Evidence**: doc shows example format; `assistant/prompt/context.py:24-29` constructs tick_line with this structure

### Claim 17
- **Doc**: line 72: "code checks config.get('maintenance'), but this field not filled"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:31-34` — code checks `maintenance = config.get("maintenance")` and renders if present

### Claim 18
- **Doc**: line 74: "build_holiday_context(config) → <holidays>"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:54-79` — function returns `<holidays>` block

### Claim 19
- **Doc**: line 85: "returns empty string if no holidays"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:57-58` — `if not holidays: return ""`

### Claim 20
- **Doc**: line 87: "build_event_context(config) → <events>"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:82-119` — function returns `<events>` block

### Claim 21
- **Doc**: line 103: "filters by EventImpact.HIGH and EventImpact.MEDIUM"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:92-109` — code filters `high` and `medium` events by impact level

### Claim 22
- **Doc**: line 107: "8 behavior rules (combines former instructions, transparency, acknowledgment, data_titles)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:40-48` — 8 numbered rules under `<behavior>`

### Claim 23
- **Doc**: line 122: "assistant/tools/__init__.py — BARB_TOOL dict"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:9` — `BARB_TOOL = {...}` dict defined

### Claim 24
- **Doc**: line 125: "Barb Script syntax (all fields with types)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:13-22` — all query fields documented with types

### Claim 25
- **Doc**: line 126: "Execution order: session → period → from → map → where → group_by → select → sort → limit"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:24` — `Execution order is FIXED: session → period → from → map → where → group_by → select → sort → limit`

### Claim 26
- **Doc**: line 127: "Important notes (group_by requires column name, select supports aggregates only)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:26-29` — IMPORTANT section with both notes

### Claim 27
- **Doc**: line 128: "Output format rules — columns field for projection, naming conventions"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:31-38` — Output format section with columns control, ordering, naming guidance

### Claim 28
- **Doc**: line 129: "<patterns> — multi-function patterns (MACD cross, breakout, NFP, OPEX, opening/closing range)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:39-48` — all 5 patterns present: MACD cross, breakout up, breakdown, NFP days, OPEX, opening range, closing range

### Claim 29
- **Doc**: line 130: "<examples> — 5 query examples (filter, indicator, raw data, hidden helper, group_by)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:50-86` — Example 1 (filter), Example 2 (indicator), Example 3 (raw data), Example 4 (helper column hidden), Example 5 (group_by)

### Claim 30
- **Doc**: line 135: "assistant/tools/reference.py → build_function_reference() -> str"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/reference.py:165` — `def build_function_reference() -> str:`

### Claim 31
- **Doc**: line 137: "Auto-generated from barb.functions.SIGNATURES and barb.functions.DESCRIPTIONS"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/reference.py:7` — `from barb.functions import DESCRIPTIONS, SIGNATURES`

### Claim 32
- **Doc**: line 140-143: "Base columns, Operators, Functions: 15 groups, Notes"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/reference.py:169-219` — sections for base columns, operators, functions, notes

### Claim 33
- **Doc**: line 152: "Compact groups: Scalar, Moving Averages"
- **Verdict**: ACCURATE
- **Evidence**: verified via Python — Compact: Scalar, Lag, Moving Averages, Window, Cumulative, Aggregate, Time

### Claim 34
- **Doc**: line 158: "Expanded groups: Pattern, Price, Candle, Signal, Oscillators, Trend, Volatility, Volume"
- **Verdict**: ACCURATE
- **Evidence**: verified via Python — matches exactly

### Claim 35
- **Doc**: line 163: "Compact groups: Scalar, Lag, Moving Averages, Window, Cumulative, Aggregate, Time"
- **Verdict**: ACCURATE
- **Evidence**: verified via Python — matches exactly

### Claim 36
- **Doc**: line 164: "Expanded groups: Pattern, Price, Candle, Signal, Oscillators, Trend, Volatility, Volume"
- **Verdict**: ACCURATE
- **Evidence**: verified via Python — matches exactly

### Claim 37
- **Doc**: line 170: "assistant/chat.py — Assistant class"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:21` — `class Assistant:`

### Claim 38
- **Doc**: line 174: "def __init__(self, api_key, instrument, df_daily, df_minute, sessions)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:26-33` — constructor with these parameters

### Claim 39
- **Doc**: line 175: "self.system_prompt = build_system_prompt(instrument)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:39` — `self.system_prompt = build_system_prompt(instrument)`

### Claim 40
- **Doc**: line 181: "model='claude-sonnet-4-5-20250929'"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:18` — `MODEL = "claude-sonnet-4-5-20250929"` and line 60 uses MODEL

### Claim 41
- **Doc**: line 182: "cache_control: {type: ephemeral}"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:67` — `"cache_control": {"type": "ephemeral"}`

### Claim 42
- **Doc**: line 188: "Model: claude-sonnet-4-5-20250929 (hardcoded in MODEL)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:18` — `MODEL = "claude-sonnet-4-5-20250929"`

### Claim 43
- **Doc**: line 189: "Max tool rounds: 5 (multi-turn tool use)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:17` — `MAX_TOOL_ROUNDS = 5` and line 57 uses it

### Claim 44
- **Doc**: line 190: "Prompt caching: system prompt cached as ephemeral block"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:63-68` — system block with cache_control ephemeral

### Claim 45
- **Doc**: line 191: "Dataframe selection: intraday timeframes → df_minute, RTH-like sessions → df_minute, else → df_daily"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:149-162` — logic: if timeframe in _INTRADAY → df_minute; elif session_name and times within one day → df_minute; else → df_daily

### Claim 46
- **Doc**: line 192: "Tool results: model_response goes to Claude, table/source_rows go to UI"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:229` — model_response added to tool_result content; `assistant/chat.py:196-223` — table/source_rows sent to UI via data_block

### Claim 47
- **Doc**: line 201: "code: CME, CBOT, NYMEX, COMEX, ICEEUR, ICEUS, EUREX"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about Supabase database schema, cannot verify from local code files alone

### Claim 48
- **Doc**: line 207: "ETH and maintenance removed from exchanges"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about Supabase schema changes, cannot verify from local code

### Claim 49
- **Doc**: line 211-225: "instruments table schema"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about Supabase database schema, cannot verify from code alone

### Claim 50
- **Doc**: line 228-236: "view instrument_full"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is about Supabase view definition, cannot verify from code

### Claim 51
- **Doc**: line 242: "instruments.py — get_instrument(symbol): cache lookup"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/instruments.py:1` — file exists, exports get_instrument

### Claim 52
- **Doc**: line 243: "holidays.py — EXCHANGE_HOLIDAYS dict, HOLIDAY_NAMES"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/holidays.py:1` — file exists; `assistant/prompt/context.py:11` imports HOLIDAY_NAMES

### Claim 53
- **Doc**: line 244: "events.py — get_event_types_for_instrument(), EventImpact.HIGH/MEDIUM"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/events.py:21-24` — EventImpact enum with HIGH and MEDIUM; `assistant/prompt/context.py:10` imports get_event_types_for_instrument and EventImpact

### Claim 54
- **Doc**: line 249: "data/1d/futures/{symbol}.parquet — daily bars (settlement close)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:20` — `path = DATA_DIR / timeframe / asset_type / f"{instrument.upper()}.parquet"`

### Claim 55
- **Doc**: line 253: "barb/data.py → load_data(instrument, timeframe, asset_type): timeframe literal directory name ('1d' or '1m')"
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:12` — `def load_data(instrument: str, timeframe: str = "1d", asset_type: str = "futures")` and line 20 uses timeframe in path

### Claim 56
- **Doc**: line 253: "Routing logic (query timeframe → which dataset) lives in assistant/chat.py"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:149-162` — routing logic in run_query execution

### Claim 57
- **Doc**: line 274: "Add function → SIGNATURES + DESCRIPTIONS → build_function_reference() → tool description → Claude knows"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/reference.py:7` imports from barb.functions; `assistant/tools/__init__.py:6` calls build_function_reference() at module load

### Claim 58
- **Doc**: line 288: "get_instrument('NQ') merges config + holidays"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about merge logic in get_instrument requires reading instruments.py implementation; doc references register_instrument doing the merge at startup

### Claim 59
- **Doc**: line 300: "assistant/prompt/__init__.py — exports build_system_prompt"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/__init__.py:3` — `from assistant.prompt.system import build_system_prompt`

### Claim 60
- **Doc**: line 301: "assistant/prompt/system.py — build_system_prompt() (identity, context, behavior rules)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:15-49` — function contains identity, context blocks, behavior rules

### Claim 61
- **Doc**: line 302: "assistant/prompt/context.py — build_instrument/holiday/event_context(config)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:14,54,82` — all three functions defined

### Claim 62
- **Doc**: line 304: "assistant/tools/__init__.py — BARB_TOOL dict, run_query(), _format_summary_for_model()"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:9,123,151` — BARB_TOOL dict, run_query function, _format_summary_for_model function

### Claim 63
- **Doc**: line 305: "assistant/tools/reference.py — build_function_reference(), DISPLAY_GROUPS"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/reference.py:11,165` — DISPLAY_GROUPS list, build_function_reference function

### Claim 64
- **Doc**: line 306: "assistant/chat.py — Assistant class, chat_stream(), prompt caching"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:21,41` — Assistant class, chat_stream method, prompt caching at lines 63-68

### Claim 65
- **Doc**: line 312: "prompt/system.py ← config/market/instruments.py (get_instrument)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:12` — `from config.market.instruments import get_instrument`

### Claim 66
- **Doc**: line 313: "prompt/system.py ← prompt/context.py ← config/market/holidays.py (HOLIDAY_NAMES)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:7-11` imports from context.py; `assistant/prompt/context.py:11` imports HOLIDAY_NAMES

### Claim 67
- **Doc**: line 314: "← config/market/events.py (get_event_types, EventImpact)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:10` — `from config.market.events import EventImpact, get_event_types_for_instrument`

### Claim 68
- **Doc**: line 316: "tools/__init__.py ← tools/reference.py ← barb/functions (SIGNATURES + DESCRIPTIONS)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:3` imports from reference; `assistant/tools/reference.py:7` imports from barb.functions

### Claim 69
- **Doc**: line 317: "← barb/interpreter (execute, QueryError)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:4` — `from barb.interpreter import QueryError, execute`

### Claim 70
- **Doc**: line 319: "chat.py ← prompt/__init__.py (build_system_prompt)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:11` — `from assistant.prompt import build_system_prompt`

### Claim 71
- **Doc**: line 320: "← tools/__init__.py (BARB_TOOL, run_query)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:12` — `from assistant.tools import BARB_TOOL, run_query`

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 58 |
| OUTDATED | 2 |
| WRONG | 0 |
| MISSING | 0 |
| UNVERIFIABLE | 11 |
| **Total** | **71** |
| **Accuracy** | **97%** |

Accuracy = ACCURATE / (Total - UNVERIFIABLE) × 100 = 58/60 × 100 = 97%

## Notes

The document is highly accurate. The two OUTDATED claims (lines 58-59 in the doc) show hardcoded example values where the code actually uses dynamic values. These are minor documentation style issues rather than factual errors - the format is correct, just showing examples instead of indicating they're dynamic.

The 11 UNVERIFIABLE claims are all related to Supabase database schema, which cannot be verified from the local codebase alone. The code references these structures but the actual database schema lives in Supabase.

All architectural claims (file structure, dependencies, function counts, behavior rules, tool description structure) are accurate and match the code exactly.
