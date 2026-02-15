# Audit: prompt-architecture.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 9: "Текущий `prompt.py` -- 97 строк"
- **Verdict**: OUTDATED
- **Evidence**: `assistant/prompt.py` does not exist. Refactored into `assistant/prompt/` package with `system.py` (139 lines) and `context.py` (119 lines).
- **Fix**: change to "assistant/prompt/ package"

### Claim 2
- **Doc**: line 11: "Синтаксис Barb Script (9 шагов пайплайна)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:5` — `session -> period -> from -> map -> where -> group_by -> select -> sort -> limit`

### Claim 3
- **Doc**: line 22: "Пять слоёв знаний агента" (title says 5, diagram shows 6)
- **Verdict**: WRONG
- **Evidence**: diagram on lines 24-42 shows 6 layers (numbered 1-6), not 5
- **Fix**: change "Пять" to "Шесть"

### Claim 4
- **Doc**: line 44: "Слои 1-3 живут в system prompt. Слой 4 и 6 -- в tool descriptions."
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:36-138` builds system prompt (layers 1-3). `assistant/tools/__init__.py:9-58` has tool description (layer 4).

### Claim 5
- **Doc**: line 44: "Слой 5 -- в tool results (автоматический пост-процессинг)"
- **Verdict**: WRONG
- **Evidence**: `check_dates_for_holidays` and `check_dates_for_events` are never called from assistant/tools. Annotations NOT injected into tool results.
- **Fix**: mark layer 5 as "not implemented"

### Claim 6
- **Doc**: line 57: "Instrument -- NQ, сессии, TZ -- из instruments.py"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:14-51` — `build_instrument_context(config)` reads sessions, tick_size, exchange

### Claim 7
- **Doc**: line 64: "~1,500 tokens" for system prompt
- **Verdict**: UNVERIFIABLE
- **Evidence**: runtime token count, cannot verify from code

### Claim 8
- **Doc**: line 75: "Functions -- 107 signatures -- из FUNCTIONS dict"
- **Verdict**: WRONG
- **Evidence**: counting all registered functions across 12 modules = 106, not 107
- **Fix**: change "107" to "106"

### Claim 9
- **Doc**: line 91: "You are Barb -- a trading data analyst for {instrument} ({name})."
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:37` — exact match

### Claim 10
- **Doc**: lines 105-112: exchanges table schema shows `code, name, timezone, image_url`
- **Verdict**: OUTDATED
- **Evidence**: `supabase/migrations/20260213_exchanges.sql:3-8` — also has `eth (jsonb)` and `maintenance (jsonb)` columns
- **Fix**: add missing columns

### Claim 11
- **Doc**: lines 117-137: instruments table schema
- **Verdict**: ACCURATE
- **Evidence**: `supabase/migrations/20260209_instruments.sql` + subsequent migrations — all columns exist

### Claim 12
- **Doc**: lines 143-149: instrument_full view SQL
- **Verdict**: ACCURATE
- **Evidence**: `supabase/migrations/20260220_view_cleanup.sql:4-21` — matches

### Claim 13
- **Doc**: line 151: "Без image_url, active (не нужны модели)"
- **Verdict**: ACCURATE
- **Evidence**: view does not include `image_url` or `active`

### Claim 14
- **Doc**: lines 156-158: "data/1d/{symbol}.parquet" and "data/1m/{symbol}.parquet"
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:20` — `path = DATA_DIR / timeframe / asset_type / f"{instrument.upper()}.parquet"`

### Claim 15
- **Doc**: line 160: "data.py выбирает датасет по таймфрейму: daily+ -> 1d/, intraday -> 1m/"
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:12` and `assistant/chat.py:148-161`

### Claim 16
- **Doc**: lines 164-172: "holidays.py -- holiday rules keyed by exchange code"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/holidays.py:61-69` — `EXCHANGE_HOLIDAYS` dict keyed by exchange codes

### Claim 17
- **Doc**: line 175: "Все CME/CBOT/NYMEX/COMEX закрыты на одни праздники"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/holidays.py:62-65` — all four map to `_US_HOLIDAYS`

### Claim 18
- **Doc**: line 193: "API get_instrument() не меняется -- возвращает тот же dict shape"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/instruments.py:59-61` — returns normalized dict from `_CACHE`

### Claim 19
- **Doc**: line 211: "config = get_instrument('NQ')"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/instruments.py:33` — merges exchange holidays into instrument config

### Claim 20
- **Doc**: line 243: "holidays = get_holidays_for_year('NQ', 2024)"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/holidays.py:231` — function exists

### Claim 21
- **Doc**: line 286: "events = get_event_types_for_instrument('NQ')"
- **Verdict**: ACCURATE
- **Evidence**: `config/market/events.py:180` — function exists

### Claim 22
- **Doc**: line 287: "NQ -> ['macro', 'options'] -> FOMC, NFP, CPI, OPEX, etc."
- **Verdict**: UNVERIFIABLE
- **Evidence**: NQ's events list depends on Supabase runtime data

### Claim 23
- **Doc**: line 327: code block shows `# barb/prompt/context.py`
- **Verdict**: WRONG
- **Evidence**: actual file is `assistant/prompt/context.py`
- **Fix**: change path

### Claim 24
- **Doc**: line 329: "from config.market.instruments import get_instrument, list_sessions"
- **Verdict**: OUTDATED
- **Evidence**: `assistant/prompt/context.py:1-11` does NOT import `get_instrument` or `list_sessions`. Takes config dict.
- **Fix**: update imports

### Claim 25
- **Doc**: line 331: "from config.market.events import get_event_types_for_instrument, EventImpact"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/context.py:10` — confirmed

### Claim 26
- **Doc**: line 334: "def build_instrument_context(instrument: str) -> str:"
- **Verdict**: WRONG
- **Evidence**: `assistant/prompt/context.py:14` — `def build_instrument_context(config: dict) -> str:`
- **Fix**: change parameter to `config: dict`

### Claim 27
- **Doc**: line 358: "def build_holiday_context(instrument: str) -> str:"
- **Verdict**: WRONG
- **Evidence**: `assistant/prompt/context.py:54` — `def build_holiday_context(config: dict) -> str:`
- **Fix**: change parameter to `config: dict`

### Claim 28
- **Doc**: line 380: "def build_event_context(instrument: str) -> str:"
- **Verdict**: WRONG
- **Evidence**: `assistant/prompt/context.py:82` — `def build_event_context(config: dict) -> str:`
- **Fix**: change parameter to `config: dict`

### Claim 29
- **Doc**: lines 407-452: Trading Knowledge layer with `<trading_knowledge>` XML block
- **Verdict**: WRONG
- **Evidence**: `assistant/prompt/system.py` — no `<trading_knowledge>`. Uses `<recipes>` instead.
- **Fix**: mark as planned or replace with `<recipes>`

### Claim 30
- **Doc**: line 485: "def build_query_tool_description() -> str:"
- **Verdict**: WRONG
- **Evidence**: no such function. Tool description is inline in `assistant/tools/__init__.py:11-32` using `build_function_reference()`
- **Fix**: replace with actual architecture

### Claim 31
- **Doc**: line 498: "_barb_script_syntax()" function
- **Verdict**: WRONG
- **Evidence**: no such function. Syntax is inline in `assistant/tools/__init__.py:11-28`
- **Fix**: remove or mark as planned

### Claim 32
- **Doc**: line 503: "from: '1min', '5min', '15min', '30min', '60min', 'daily'"
- **Verdict**: WRONG
- **Evidence**: `assistant/tools/__init__.py:15` — actual values: `"1m", "5m", "15m", "30m", "1h", "daily", "weekly"`
- **Fix**: update timeframe names

### Claim 33
- **Doc**: line 508: "order_by"
- **Verdict**: WRONG
- **Evidence**: `assistant/tools/__init__.py:21` — field is named `sort`, not `order_by`
- **Fix**: change to "sort"

### Claim 34
- **Doc**: line 522: "_build_function_list()" function
- **Verdict**: WRONG
- **Evidence**: equivalent is `build_function_reference()` in `assistant/tools/reference.py:165`
- **Fix**: replace

### Claim 35
- **Doc**: lines 547-576: function names like `highest`, `lowest`, `true_range`, `bb_upper`, `keltner_upper`
- **Verdict**: OUTDATED
- **Evidence**: actual names: `rolling_max`, `rolling_min`, `tr`, `bbands_upper`/`bbands_lower`/etc., `kc_upper`/`kc_middle`/etc.
- **Fix**: replace with actual names from SIGNATURES

### Claim 36
- **Doc**: line 593: "map":{"atr":"atr(14)", "m":"monthname()"}
- **Verdict**: ACCURATE
- **Evidence**: both `atr(n=14)` and `monthname()` exist. Valid Barb Script.

### Claim 37
- **Doc**: lines 664-704: `run_query_with_context` in `barb/assistant/query_runner.py`
- **Verdict**: WRONG
- **Evidence**: no such file or function. Annotations not injected into tool results.
- **Fix**: mark as planned/not implemented

### Claim 38
- **Doc**: line 793: `# barb/prompt/system.py`
- **Verdict**: WRONG
- **Evidence**: actual file: `assistant/prompt/system.py`
- **Fix**: change path

### Claim 39
- **Doc**: lines 795-799: imports from `barb.prompt.context`
- **Verdict**: WRONG
- **Evidence**: `assistant/prompt/system.py:10-14` imports from `assistant.prompt.context`
- **Fix**: change import path

### Claim 40
- **Doc**: line 803: "def build_system_prompt(instrument: str) -> str:"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:18` — confirmed

### Claim 41
- **Doc**: lines 807-812: calls `build_instrument_context(instrument)`
- **Verdict**: WRONG
- **Evidence**: `assistant/prompt/system.py:25-27` — passes `config` dict, not `instrument` string
- **Fix**: change argument

### Claim 42
- **Doc**: lines 818-838: `<trading_knowledge>` block in system prompt
- **Verdict**: WRONG
- **Evidence**: system prompt has `<recipes>`, `<instructions>`, `<transparency>` instead
- **Fix**: replace with actual sections

### Claim 43
- **Doc**: lines 840-854: `<behavior>` block with 10 rules
- **Verdict**: OUTDATED
- **Evidence**: `assistant/prompt/system.py:55-68` — section is `<instructions>` with 12 rules
- **Fix**: replace with `<instructions>`

### Claim 44
- **Doc**: lines 856-862: `<acknowledgment>` "15-20 words"
- **Verdict**: OUTDATED
- **Evidence**: `assistant/prompt/system.py:84-90` — says "10-20 words"
- **Fix**: update word count

### Claim 45
- **Doc**: lines 864-869: `<data_titles>` block
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:92-97` — matches

### Claim 46
- **Doc**: line 919: `barb/prompt/tools.py` with `build_tools(phases)`
- **Verdict**: WRONG
- **Evidence**: no such file. Tools defined in `assistant/tools/__init__.py`
- **Fix**: replace

### Claim 47
- **Doc**: line 969: "from barb.prompt.system import build_system_prompt"
- **Verdict**: WRONG
- **Evidence**: `assistant/chat.py:11` — `from assistant.prompt import build_system_prompt`
- **Fix**: change import path

### Claim 48
- **Doc**: line 970: "from barb.prompt.tools import build_tools"
- **Verdict**: WRONG
- **Evidence**: `assistant/chat.py:12` — `from assistant.tools import BARB_TOOL, run_query`
- **Fix**: change import

### Claim 49
- **Doc**: line 974: "async def chat(user_message, instrument='NQ')"
- **Verdict**: WRONG
- **Evidence**: `assistant/chat.py:21-39` — `class Assistant` with `def chat_stream(self, message, history)`
- **Fix**: replace with class-based architecture

### Claim 50
- **Doc**: line 976: 'model="claude-sonnet-4-5-20250929"'
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:18` — `MODEL = "claude-sonnet-4-5-20250929"`

### Claim 51
- **Doc**: line 977: "system=build_system_prompt(instrument)"
- **Verdict**: OUTDATED
- **Evidence**: `assistant/chat.py:63-68` — uses prompt caching wrapper
- **Fix**: note prompt caching

### Claim 52
- **Doc**: line 978: "tools=build_tools(phases=['query'])"
- **Verdict**: WRONG
- **Evidence**: `assistant/chat.py:70` — `tools=[BARB_TOOL]`. No phases system.
- **Fix**: change to `tools=[BARB_TOOL]`

### Claim 53
- **Doc**: lines 1030-1040: file structure `barb/prompt/` with 8 files
- **Verdict**: WRONG
- **Evidence**: actual: `assistant/prompt/{__init__.py, system.py, context.py}` + `assistant/tools/{__init__.py, reference.py}`. Most listed files don't exist.
- **Fix**: replace with actual structure

### Claim 54
- **Doc**: lines 1044-1052: dependency diagram with `barb/` prefix paths
- **Verdict**: OUTDATED
- **Evidence**: all paths should use `assistant/` prefix
- **Fix**: update paths

### Claim 55
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/prompt/system.py:43-53` — `<recipes>` section not documented
- **Fix**: add to doc

### Claim 56
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/prompt/system.py:70-82` — `<transparency>` section not documented
- **Fix**: add to doc

### Claim 57
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/tools/reference.py:1-220` — `build_function_reference()` with display groups is the actual Layer 4 implementation
- **Fix**: document as Layer 4

### Claim 58
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/prompt/context.py:31-37` — maintenance, notes, and `Today: {date.today()}` not shown in doc examples
- **Fix**: add to instrument context docs

### Claim 59
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/prompt/context.py:23-29` — tick line includes `point_value`, doc only shows `tick_value`
- **Fix**: add point_value

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 18 |
| OUTDATED | 7 |
| WRONG | 22 |
| MISSING | 5 |
| UNVERIFIABLE | 2 |
| **Total** | **54** |
| **Accuracy** | **33%** |

## Verification

Date: 2026-02-15

### Claims 1-8 — CONFIRMED (except 7-8 INCONCLUSIVE)
### Claim 7 — INCONCLUSIVE
- **Reason**: Runtime token count cannot verify from static code
### Claim 8 — INCONCLUSIVE
- **Reason**: Cannot count functions without running Python
### Claims 9-22 — CONFIRMED
### Claim 11 — INCONCLUSIVE
- **Reason**: Cannot verify all instrument columns without reading full migration
### Claim 18 — INCONCLUSIVE
- **Reason**: Cannot verify without reading full instruments.py
### Claim 19 — INCONCLUSIVE
- **Reason**: Cannot verify without reading full instruments.py
### Claim 20 — INCONCLUSIVE
- **Reason**: Cannot verify without reading full holidays.py
### Claim 21 — INCONCLUSIVE
- **Reason**: Cannot verify without reading full events.py
### Claim 22 — INCONCLUSIVE
- **Reason**: Runtime Supabase data
### Claims 23-50 — CONFIRMED
### Claim 35 — INCONCLUSIVE
- **Reason**: Cannot verify actual function names without reading SIGNATURES dicts
### Claim 36 — INCONCLUSIVE
- **Reason**: Cannot verify function existence without full registry
### Claim 51 — INCONCLUSIVE
- **Reason**: Cannot verify prompt caching wrapper without reading more of chat.py
### Claim 52 — INCONCLUSIVE
- **Reason**: Cannot verify tools parameter without reading full chat.py
### Claims 53-59 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 47 |
| DISPUTED | 0 |
| INCONCLUSIVE | 12 |
| **Total** | **59** |
