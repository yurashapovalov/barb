# Audit: assistant.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 3: "LLM-слой. Anthropic Claude с tool calling."
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:8` — `import anthropic`; line 59-72 uses `self.client.messages.stream(... tools=[BARB_TOOL])`

### Claim 2
- **Doc**: line 21: "Максимум 5 раундов tool calling за один запрос."
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:17` — `MAX_TOOL_ROUNDS = 5`

### Claim 3
- **Doc**: line 26: "Класс `Assistant`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:21` — `class Assistant:`

### Claim 4
- **Doc**: line 26: "Использует `anthropic.Anthropic` клиент"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:34` — `self.client = anthropic.Anthropic(api_key=api_key)`

### Claim 5
- **Doc**: line 26: "с prompt caching"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:67` — `"cache_control": {"type": "ephemeral"}`

### Claim 6
- **Doc**: line 26: "Стримит ответ через generator, yielding SSE events: text_delta, tool_start, tool_end, data_block, done"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:91,134,177,211,254` — yields all 5 event types

### Claim 7
- **Doc**: line 29: "model: `claude-sonnet-4-5-20250929`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:18` — `MODEL = "claude-sonnet-4-5-20250929"`

### Claim 8
- **Doc**: line 30: "max_tokens: 4096"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:61` — `max_tokens=4096`

### Claim 9
- **Doc**: line 31: "temperature: 0"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:62` — `temperature=0`

### Claim 10
- **Doc**: line 33: "### prompt.py" (single file)
- **Verdict**: OUTDATED
- **Evidence**: `assistant/prompt/__init__.py:1` — now a package with `system.py` and `context.py`
- **Fix**: change to "### prompt/" package

### Claim 11
- **Doc**: line 34: "Строит system prompt из конфига инструмента"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:18` — `def build_system_prompt(instrument: str) -> str:`

### Claim 12
- **Doc**: line 35: "Роль и контекст (символ, биржа, диапазон данных, сессии)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:37` and `context.py:40-51` — includes all listed context

### Claim 13
- **Doc**: line 36: "Инструкции по workflow"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:55-68` — `<instructions>` section

### Claim 14
- **Doc**: line 37: "модель пишет 15-20 слов перед tool call"
- **Verdict**: WRONG
- **Evidence**: `assistant/prompt/system.py:85` — `brief confirmation (10-20 words)`, not 15-20
- **Fix**: change "15-20 слов" to "10-20 слов"

### Claim 15
- **Doc**: line 38: "Секцию `<data_titles>`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:92-97` — `<data_titles>` section exists

### Claim 16
- **Doc**: line 39: "Примеры использования"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/prompt/system.py:99-137` — `<examples>` section with 5 examples

### Claim 17
- **Doc**: line 42: "Один инструмент: run_query"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:10` — `BARB_TOOL` defines single tool `"run_query"`

### Claim 18
- **Doc**: line 44: "Принимает JSON-запрос, выполняет через interpreter"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:61-71` — `run_query()` calls `execute(query, df, sessions)`

### Claim 19
- **Doc**: line 45: "возвращает: `model_response`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:74-76` — `"model_response": _format_summary_for_model(summary)`

### Claim 20
- **Doc**: line 46: "возвращает: `table`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:77` — `"table": result.get("table")`

### Claim 21
- **Doc**: line 47: "возвращает: `source_rows`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:78` — `"source_rows": result.get("source_rows")`

### Claim 22
- **Doc**: line 49: "Tool description включает expressions.md"
- **Verdict**: OUTDATED
- **Evidence**: `assistant/tools/__init__.py:3-6` — uses `build_function_reference()` from `reference.py`, not static `expressions.md`
- **Fix**: change "expressions.md" to "auto-generated reference from `reference.py`"

### Claim 23
- **Doc**: line 53: "System prompt кэшируется через cache_control"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:67` — `"cache_control": {"type": "ephemeral"}`

### Claim 24
- **Doc**: line 53: "~90% токенов из кэша (0.30$/MTok вместо 3$/MTok)"
- **Verdict**: UNVERIFIABLE
- **Evidence**: runtime cache hit rate and pricing, cannot verify from code

### Claim 25
- **Doc**: line 57: "Каждый вызов логируется в Supabase (таблица tool_calls)"
- **Verdict**: ACCURATE
- **Evidence**: `api/main.py:220` — `db.table("tool_calls").insert(tool_rows).execute()`

### Claim 26
- **Doc**: line 58: "tool_name, input, output"
- **Verdict**: ACCURATE
- **Evidence**: `supabase/migrations/20260129_init.sql:32-34` — columns exist

### Claim 27
- **Doc**: line 59: "error (если был)"
- **Verdict**: ACCURATE
- **Evidence**: `supabase/migrations/20260129_init.sql:35` — `error text`

### Claim 28
- **Doc**: line 60: "duration_ms"
- **Verdict**: ACCURATE
- **Evidence**: `supabase/migrations/20260129_init.sql:36` — `duration_ms int`

### Claim 29
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/tools/__init__.py:79` — `run_query` also returns `"chart"` with chart hints
- **Fix**: add `chart` to return values list

### Claim 30
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/context.py:1` — sliding window + summarization module (SUMMARY_THRESHOLD=20, WINDOW_SIZE=10)
- **Fix**: add "### context.py" section

### Claim 31
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/tools/reference.py:1` — auto-generates function reference from SIGNATURES + DESCRIPTIONS
- **Fix**: add "### tools/reference.py" section

### Claim 32
- **Doc**: line 34: prompt sections listed without `<recipes>` and `<transparency>`
- **Verdict**: MISSING
- **Evidence**: `assistant/prompt/system.py:42-53,70-82` — `<recipes>` and `<transparency>` sections exist
- **Fix**: add to prompt sections list

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 21 |
| OUTDATED | 2 |
| WRONG | 1 |
| MISSING | 4 |
| UNVERIFIABLE | 1 |
| **Total** | **29** |
| **Accuracy** | **72%** |

## Verification

Date: 2026-02-15

### Claim 1 — CONFIRMED
### Claim 2 — CONFIRMED
### Claim 3 — CONFIRMED
### Claim 4 — CONFIRMED
### Claim 5 — CONFIRMED
### Claim 6 — CONFIRMED
### Claim 7 — CONFIRMED
### Claim 8 — CONFIRMED
### Claim 9 — CONFIRMED
### Claim 10 — DISPUTED
- **Auditor said**: OUTDATED
- **Should be**: OUTDATED (confirmed, but minor — heading imprecision, not functional breakage)
### Claim 11 — CONFIRMED
### Claim 12 — CONFIRMED
### Claim 13 — CONFIRMED
### Claim 14 — CONFIRMED
### Claim 15 — CONFIRMED
### Claim 16 — CONFIRMED
### Claim 17 — CONFIRMED
### Claim 18 — CONFIRMED
### Claim 19 — CONFIRMED
### Claim 20 — CONFIRMED
### Claim 21 — CONFIRMED
### Claim 22 — CONFIRMED
### Claim 23 — CONFIRMED
### Claim 24 — INCONCLUSIVE
- **Reason**: runtime metric (~90% cache hit), cannot verify from code
### Claim 25 — CONFIRMED
### Claim 26 — CONFIRMED
### Claim 27 — CONFIRMED
### Claim 28 — CONFIRMED
### Claim 29 — CONFIRMED
### Claim 30 — CONFIRMED
### Claim 31 — CONFIRMED
### Claim 32 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 29 |
| DISPUTED | 1 |
| INCONCLUSIVE | 1 |
| **Total** | **31** |
