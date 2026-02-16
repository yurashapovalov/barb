# Audit: assistant.md

**Date**: 2026-02-16
**Claims checked**: 38
**Correct**: 37 | **Wrong**: 0 | **Outdated**: 0 | **Unverifiable**: 1

## Issues

No wrong or outdated claims found. One claim is unverifiable from code alone.

### [UNVERIFIABLE] Cache hit rate ~90%
- **Doc says**: "~90% токенов читаются из кэша"
- **Code says**: Prompt caching is implemented with `cache_control: {"type": "ephemeral"}`, but actual cache hit rate depends on runtime behavior and Anthropic's caching TTL
- **File**: `assistant/chat.py:67`

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Max 5 rounds tool calling per request | CORRECT | `assistant/chat.py:17` — `MAX_TOOL_ROUNDS = 5` |
| 2 | Class name is `Assistant` | CORRECT | `assistant/chat.py:21` — `class Assistant:` |
| 3 | Uses `anthropic.Anthropic` client | CORRECT | `assistant/chat.py:34` — `self.client = anthropic.Anthropic(api_key=api_key)` |
| 4 | Streams via generator yielding SSE events | CORRECT | `assistant/chat.py:41` — `def chat_stream(...) -> Generator[dict]:` |
| 5 | SSE events: text_delta, tool_start, tool_end, data_block, done | CORRECT | `assistant/chat.py:91,133,176,211,253` — all 5 event types present |
| 6 | Model: `claude-sonnet-4-5-20250929` | CORRECT | `assistant/chat.py:18` — `MODEL = "claude-sonnet-4-5-20250929"` |
| 7 | max_tokens: 4096 | CORRECT | `assistant/chat.py:61` — `max_tokens=4096` |
| 8 | temperature: 0 | CORRECT | `assistant/chat.py:62` — `temperature=0` |
| 9 | prompt/ is a package with two files | CORRECT | `assistant/prompt/__init__.py`, `system.py`, `context.py` — `__init__.py` is just re-export, two substantive files |
| 10 | system.py has `build_system_prompt(instrument)` | CORRECT | `assistant/prompt/system.py:18` — `def build_system_prompt(instrument: str) -> str:` |
| 11 | Prompt section: role and context (symbol, exchange, data range, sessions) | CORRECT | `assistant/prompt/system.py:37-41` + `assistant/prompt/context.py:14-51` |
| 12 | Prompt section: `<recipes>` with multi-function patterns | CORRECT | `assistant/prompt/system.py:43-53` |
| 13 | Prompt section: `<instructions>` with 12 rules | CORRECT | `assistant/prompt/system.py:55-68` — exactly 12 numbered rules |
| 14 | Prompt section: `<transparency>` for alternative indicators | CORRECT | `assistant/prompt/system.py:70-82` |
| 15 | Prompt section: `<acknowledgment>` — 10-20 words before tool call | CORRECT | `assistant/prompt/system.py:84-90` |
| 16 | Prompt section: `<data_titles>` — title for each result | CORRECT | `assistant/prompt/system.py:92-97` |
| 17 | Prompt section: `<examples>` — 5 examples | CORRECT | `assistant/prompt/system.py:99-138` — examples 1-5 |
| 18 | context.py has `build_instrument_context(config)` | CORRECT | `assistant/prompt/context.py:14` |
| 19 | context.py has `build_holiday_context(config)` | CORRECT | `assistant/prompt/context.py:54` |
| 20 | context.py has `build_event_context(config)` | CORRECT | `assistant/prompt/context.py:82` |
| 21 | Top-level context.py: sliding window + summarization | CORRECT | `assistant/context.py:1` — docstring confirms |
| 22 | `SUMMARY_THRESHOLD = 20` | CORRECT | `assistant/context.py:9` |
| 23 | `WINDOW_SIZE = 10` | CORRECT | `assistant/context.py:10` |
| 24 | `build_history_with_context()` exists | CORRECT | `assistant/context.py:30` |
| 25 | `summarize()` calls Claude without tools for 3-5 sentence summary | CORRECT | `assistant/context.py:48-73` — `client.messages.create()` with no tools, prompt says "3-5 sentences" |
| 26 | Single tool: run_query | CORRECT | `assistant/tools/__init__.py:9-57` — only BARB_TOOL defined; `assistant/chat.py:70` — `tools=[BARB_TOOL]` |
| 27 | run_query returns `model_response` | CORRECT | `assistant/tools/__init__.py:75` |
| 28 | run_query returns `table` | CORRECT | `assistant/tools/__init__.py:77` |
| 29 | run_query returns `source_rows` | CORRECT | `assistant/tools/__init__.py:78` |
| 30 | run_query returns `source_row_count` | CORRECT | `assistant/tools/__init__.py:79` |
| 31 | run_query returns `chart` (category, value columns) | CORRECT | `assistant/tools/__init__.py:80` + `barb/interpreter.py:639` — `{"category": ..., "value": ...}` |
| 32 | reference.py auto-generates from SIGNATURES + DESCRIPTIONS | CORRECT | `assistant/tools/reference.py:7` — `from barb.functions import DESCRIPTIONS, SIGNATURES` |
| 33 | reference.py uses display groups (compact and expanded) | CORRECT | `assistant/tools/reference.py:11-162` — `DISPLAY_GROUPS` with expanded flag |
| 34 | Prompt caching via `cache_control: {"type": "ephemeral"}` | CORRECT | `assistant/chat.py:67` |
| 35 | Cached read costs $0.30/MTok vs $3/MTok input | CORRECT | `assistant/chat.py:231-236` — pricing matches |
| 36 | ~90% tokens read from cache | UNVERIFIABLE | Runtime behavior, depends on Anthropic's cache TTL and usage patterns |
| 37 | tool_calls table: message_id, tool_name, input, output, error, duration_ms | CORRECT | `supabase/migrations/20260129_init.sql:29-38` — all columns present |
| 38 | Tool calls logged to Supabase tool_calls table | CORRECT | `api/main.py:220` — `db.table("tool_calls").insert(tool_rows).execute()` |
