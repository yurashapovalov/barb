# Audit: prompt-architecture.md

**Date**: 2026-02-16
**Claims checked**: 68
**Correct**: 63 | **Wrong**: 3 | **Outdated**: 0 | **Unverifiable**: 2

## Issues

### [WRONG] RTH session time in example shows 09:30-17:00
- **Doc says**: `RTH 09:30-17:00` (line 71, instrument context example)
- **Code says**: NQ RTH is `["09:30", "16:15"]` per test config
- **File**: `tests/conftest.py:24`

### [WRONG] Events example omits PCE from high-impact list
- **Doc says**: High impact events listed as FOMC, NFP, CPI only (lines 94-96)
- **Code says**: PCE is also `EventImpact.HIGH` — 4 high-impact macro events, not 3
- **File**: `config/market/events.py:48`

### [WRONG] Events example shows medium impact as "PPI, GDP, Retail Sales, ..."
- **Doc says**: `Medium impact: PPI, GDP, Retail Sales, ...` (line 98)
- **Code says**: There are 8 medium-impact macro events: PPI, GDP, Retail Sales, ISM Manufacturing, ISM Services, Consumer Confidence, Michigan Sentiment, Durable Goods Orders. Also includes low-impact events (Jobless Claims, Industrial Production) which are not mentioned
- **File**: `config/market/events.py:46-57`

### [UNVERIFIABLE] Exchange list includes ICEUS and EUREX
- **Doc says**: Exchanges table contains `CME, CBOT, NYMEX, COMEX, ICEEUR, ICEUS, EUREX` (line 249)
- **Code says**: Seed migration only inserts 5 exchanges (CME, CBOT, NYMEX, COMEX, ICEEUR). ICEUS and EUREX are referenced in `holidays.py` EXCHANGE_HOLIDAYS but not in any migration. They may have been inserted directly via Supabase
- **File**: `supabase/migrations/20260213_exchanges.sql:20-25`, `config/market/holidays.py:61-68`

### [UNVERIFIABLE] RTH session time for NQ in production
- **Doc says**: RTH is `09:30-17:00` in the instrument context example
- **Code says**: Test fixture uses `09:30-16:15`. Production Supabase data may differ
- **File**: `tests/conftest.py:24`

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | System prompt file is `assistant/prompt/system.py` | CORRECT | `assistant/prompt/system.py` exists |
| 2 | Identity text: "You are Barb..." | CORRECT | `assistant/prompt/system.py:37` |
| 3 | `<instrument>` block includes symbol, sessions, tick, data range | CORRECT | `assistant/prompt/context.py:39-51` |
| 4 | `<holidays>` block includes closed/early close days | CORRECT | `assistant/prompt/context.py:54-79` |
| 5 | `<events>` block includes FOMC, NFP, OPEX with impact levels | CORRECT | `assistant/prompt/context.py:82-119` |
| 6 | `<recipes>` includes MACD cross, breakout, NFP, OPEX patterns | CORRECT | `assistant/prompt/system.py:43-53` |
| 7 | `<instructions>` has 12 behavior rules | CORRECT | `assistant/prompt/system.py:55-68` — 12 numbered rules |
| 8 | `<transparency>` section for alternative indicators | CORRECT | `assistant/prompt/system.py:70-82` |
| 9 | `<acknowledgment>` section for brief confirmation | CORRECT | `assistant/prompt/system.py:84-90` |
| 10 | `<data_titles>` section requiring title for every run_query | CORRECT | `assistant/prompt/system.py:92-97` |
| 11 | `<examples>` has 5 conversation examples | CORRECT | `assistant/prompt/system.py:99-138` — Examples 1-5 |
| 12 | Tool description is in `assistant/tools/__init__.py` | CORRECT | `assistant/tools/__init__.py:9-58` |
| 13 | `BARB_TOOL` dict contains Barb Script syntax | CORRECT | `assistant/tools/__init__.py:9` |
| 14 | Expression reference is auto-generated from barb.functions | CORRECT | `assistant/tools/__init__.py:6` calls `build_function_reference()` |
| 15 | 15 function groups in DISPLAY_GROUPS | CORRECT | `assistant/tools/reference.py:11-162` — 15 groups verified |
| 16 | 106 functions total | CORRECT | `barb/functions/__init__.py` — verified 106 FUNCTIONS |
| 17 | Compact groups (one line) and expanded groups (with description) | CORRECT | `assistant/tools/reference.py:189-199` |
| 18 | `build_system_prompt(instrument: str) -> str` signature | CORRECT | `assistant/prompt/system.py:18` |
| 19 | Called once at Assistant creation, result cached via prompt caching | CORRECT | `assistant/chat.py:39` (set in `__init__`), `chat.py:63-68` (cache_control ephemeral) |
| 20 | Identity text matches exactly | CORRECT | `assistant/prompt/system.py:37-39` matches doc lines 47-49 |
| 21 | Three context blocks from `assistant/prompt/context.py` | CORRECT | `assistant/prompt/context.py` exports 3 functions |
| 22 | Each context function takes `config: dict` | CORRECT | `context.py:14,54,82` — all take `config: dict` |
| 23 | `build_instrument_context(config)` produces `<instrument>` block | CORRECT | `context.py:39-51` |
| 24 | Instrument context includes point_value, notes, Today | CORRECT | `context.py:23-37,44` |
| 25 | Code checks `config.get("maintenance")` but field not populated | CORRECT | `context.py:31-33` checks it; `instruments.py` normalized dict has no maintenance key |
| 26 | `build_holiday_context(config)` produces `<holidays>` block | CORRECT | `context.py:54-79` |
| 27 | Holidays from `config["holidays"]` merged in `register_instrument()` | CORRECT | `instruments.py:33,53` |
| 28 | Returns empty string if no holidays | CORRECT | `context.py:57-58` |
| 29 | `build_event_context(config)` produces `<events>` block | CORRECT | `context.py:82-119` |
| 30 | Events from `get_event_types_for_instrument(symbol)` in events.py | CORRECT | `context.py:88` |
| 31 | Filters by `EventImpact.HIGH` and `EventImpact.MEDIUM` | CORRECT | `context.py:92-93` |
| 32 | RTH session time shown as 09:30-17:00 in example | WRONG | `tests/conftest.py:24` — NQ RTH is `["09:30", "16:15"]` |
| 33 | High impact example shows only FOMC, NFP, CPI | WRONG | `config/market/events.py:48` — PCE is also HIGH impact |
| 34 | Medium impact example shows PPI, GDP, Retail Sales | WRONG | `events.py:46-57` — 8 medium events plus low-impact events not mentioned |
| 35 | Recipes block content matches code | CORRECT | `assistant/prompt/system.py:43-53` matches doc lines 109-120 exactly |
| 36 | Only multi-function patterns in recipes | CORRECT | Recipe comment: "single-function descriptions are in the tool reference" |
| 37 | 12 instruction rules | CORRECT | `system.py:55-68` — numbered 1-12 |
| 38 | Rule 1: Data questions -> build query | CORRECT | `system.py:56` |
| 39 | Rule 3: Percentage -> TWO queries | CORRECT | `system.py:58` |
| 40 | Rule 6: Answer in user's language | CORRECT | `system.py:61` |
| 41 | Rule 9: dayname() not dayofweek() | CORRECT | `system.py:64` |
| 42 | Transparency section text matches | CORRECT | `system.py:70-82` matches doc lines 144-157 |
| 43 | Acknowledgment: 10-20 words before run_query | CORRECT | `system.py:85` |
| 44 | Data titles: every run_query MUST include "title" | CORRECT | `system.py:93` |
| 45 | 5 examples: simple filter, indicator, event, holiday, follow-up | CORRECT | `system.py:99-138` |
| 46 | `BARB_TOOL` dict in `assistant/tools/__init__.py` | CORRECT | `tools/__init__.py:9` |
| 47 | Tool description includes Barb Script syntax with all fields | CORRECT | `tools/__init__.py:11-31` |
| 48 | Execution order: session -> period -> from -> map -> where -> group_by -> select -> sort -> limit | CORRECT | `tools/__init__.py:24` |
| 49 | group_by requires column name, select supports aggregates only | CORRECT | `tools/__init__.py:27-28` |
| 50 | `build_function_reference() -> str` in reference.py | CORRECT | `assistant/tools/reference.py:165` |
| 51 | Auto-generated from SIGNATURES and DESCRIPTIONS | CORRECT | `reference.py:7` imports from `barb.functions` |
| 52 | Base columns: open, high, low, close, volume | CORRECT | `reference.py:174` |
| 53 | Operators: arithmetic, comparison, boolean, membership | CORRECT | `reference.py:179-183` |
| 54 | Notes about OHLCV auto-use, NaN, dayofweek 0-4 | CORRECT | `reference.py:205-217` |
| 55 | Compact groups: Scalar, Lag, Moving Averages, Window, Cumulative, Aggregate, Time | CORRECT | Verified via Python — matches exactly |
| 56 | Expanded groups: Pattern, Price, Candle, Signal, Oscillators, Trend, Volatility, Volume | CORRECT | Verified via Python — matches exactly |
| 57 | `Assistant.__init__` takes api_key, instrument, df_daily, df_minute, sessions | CORRECT | `chat.py:26-33` |
| 58 | Model is `claude-sonnet-4-5-20250929` hardcoded in `MODEL` | CORRECT | `chat.py:18` |
| 59 | Max tool rounds: 5 | CORRECT | `chat.py:17` — `MAX_TOOL_ROUNDS = 5` |
| 60 | Prompt caching: system prompt cached as ephemeral block | CORRECT | `chat.py:63-68` |
| 61 | Dataframe selection: intraday -> df_minute, session -> logic, else -> df_daily | CORRECT | `chat.py:148-161` |
| 62 | Tool results: model_response to Claude, table/source_rows to UI | CORRECT | `chat.py:162-211` |
| 63 | Exchanges table: code, name, timezone, image_url | CORRECT | After all migrations (20260213 + 20260215 + 20260216 + 20260217) |
| 64 | Exchange codes: CME, CBOT, NYMEX, COMEX, ICEEUR, ICEUS, EUREX | UNVERIFIABLE | Seed has 5; ICEUS/EUREX may be in Supabase directly |
| 65 | Instruments table schema matches doc | CORRECT | After all migrations — matches doc listing (minus created_at/updated_at) |
| 66 | instrument_full view matches doc | CORRECT | `20260220_view_cleanup.sql` matches doc exactly |
| 67 | `load_data(instrument, timeframe, asset_type)` in barb/data.py | CORRECT | `barb/data.py:12` |
| 68 | File structure and dependency tree | CORRECT | All files exist, all imports verified |
