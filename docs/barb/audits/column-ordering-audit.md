# Audit: column-ordering.md

Date: 2026-02-16

## Claims

### Claim 1
- **Doc**: line 7-9: "Модель указывает `columns` в запросе. Interpreter показывает ровно эти колонки в указанном порядке. Без дополнений, без OHLCV по умолчанию."
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:524-529` — if `columns` exists in query, filters DataFrame to only those columns in that order: `if columns: cols = [c for c in columns if c in df.columns]; if cols: return df[cols]`

### Claim 2
- **Doc**: line 11: "Правило порядка в промпте: `date/time first, then answer columns (from map), then supporting context (close, volume)`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:35` — "Order: date/time first, then answer columns (from map), then supporting context (close, volume)."

### Claim 3
- **Doc**: line 13: "Технически projection применяется ко всем DataFrame результатам (включая grouped). Но для grouped результатов колонки из `columns` обычно не совпадают с реальными (group key + aggregate) → fallback. Промпт говорит: 'Omit columns for scalar/grouped results.'"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:524-529` — projection code runs for all DataFrames (no special handling for grouped); `assistant/tools/__init__.py:36` — "Omit columns for scalar/grouped results (they manage their own output)."

### Claim 4
- **Doc**: line 17-27: "Fallback — колонки выводятся в фиксированном порядке: 1. date 2. time 3. group keys 4. calculated 5. OHLC 6. volume 7. remaining"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:531-557` — fallback logic: ordered list starts with date (538), time (540), group_cols (542-544), map_columns (545-547), _OHLC_COLUMNS (548-550), volume (551-552), remaining (553-555)

### Claim 5
- **Doc**: line 23: "calculated — колонки из map, в порядке объявления (перед OHLC — derived data важнее сырых свечей)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:532,545-547` — map_columns = list(query.get("map", {}).keys()) preserves insertion order (dicts preserve order in Python 3.7+); added before OHLC_COLUMNS in ordering loop

### Claim 6
- **Doc**: line 31-36: "timestamp разбивается на date и time" with table showing intraday gets both, daily+ gets only date
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:515-522` — if "timestamp" exists: creates "date" with strftime("%Y-%m-%d"); if `timeframe in _INTRADAY_TIMEFRAMES` creates "time" with strftime("%H:%M"); drops timestamp column

### Claim 7
- **Doc**: line 35: "1m, 5m, 15m, 30m, 1h, 2h, 4h" are intraday timeframes
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:50` — `_INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}`

### Claim 8
- **Doc**: line 36: "daily, weekly, monthly, quarterly, yearly" get only date
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:50,520-521` — these timeframes are NOT in `_INTRADAY_TIMEFRAMES`, so time column is not created (only date)

### Claim 9
- **Doc**: line 38: "Модель пишет `date` в `columns` — interpreter знает как его создать из timestamp"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:517-522` — timestamp is split into date/time before projection (line 515-522), then projection filters columns (line 524-529), so "date" is available even if not originally in DataFrame

### Claim 10
- **Doc**: line 82-86: "_prepare_for_output(): 1. Split timestamp → date/time 2. Если columns есть → projection 3. Иначе → fallback ordering"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:499-557` — function starts at line 499; steps are: reset_index (513), split timestamp (515-522), projection if columns exists (524-529), else fallback (531-557)

### Claim 11
- **Doc**: line 88: "Вызывается в _build_response() перед сериализацией. Валидация формата columns (должен быть массив строк) — в barb/validation.py"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:616,621` — `_prepare_for_output()` called in `_build_response()` before `_serialize_records()` (lines 616-617, 621-622); `barb/validation.py:103-113` — validates columns must be list of strings

### Claim 12
- **Doc**: line 90-92: "PostgreSQL JSONB не сохраняет порядок ключей. Бэкенд (assistant/chat.py) извлекает порядок колонок из сериализованных записей и передаёт как columns в data_block"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:201-209` — comment says "Column order from _order_columns() — JSONB doesn't preserve key order"; extracts columns as `list(ui_data[0].keys())` and includes in block as "columns": columns

### Claim 13
- **Doc**: line 92: "Фронтенд (data-panel.tsx) использует `columnOrder ?? Object.keys(rows[0])` — приоритет у columns из бэкенда"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/panels/data-panel.tsx:60-62` — buildColumns function accepts `columnOrder?: string[] | null` parameter; line 62: `const keys = columnOrder ?? Object.keys(rows[0])`; line 107: calls `buildColumns(rows, data.columns)` passing backend columns

### Claim 14
- **Doc**: line 96: "OHLCV колонки (_PRESERVE_PRECISION) сохраняют оригинальную точность"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:56` — `_PRESERVE_PRECISION = {"open", "high", "low", "close", "volume"}`; lines 577-578, 582-583: values with keys in `_PRESERVE_PRECISION` are not rounded

### Claim 15
- **Doc**: line 96: "Все остальные float колонки округляются до CALCULATED_PRECISION = 4"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:59` — `CALCULATED_PRECISION = 4`; lines 579-580, 584-585: float values NOT in `_PRESERVE_PRECISION` are rounded to CALCULATED_PRECISION

### Claim 16
- **Doc**: line 98: "Обрабатывается в _serialize_records() при конвертации DataFrame → JSON"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:560-589` — `_serialize_records()` function converts DataFrame records to JSON format; precision handling at lines 575-585

### Claim 17
- **Doc**: line 50: projection example result "date | chg | close"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:524-529` — projection returns df[cols] where cols is filtered by columns array in exact order from query

### Claim 18
- **Doc**: line 62: "cross использовался для фильтра, но скрыт" when columns omits it
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:524-529` — projection only includes columns listed in the `columns` array; computed map columns not in the array are excluded from output

### Claim 19
- **Doc**: line 70: fallback без columns shows "date | chg | open | high | low | close | volume"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:531-557` — fallback ordering: date first (538-539), then map_columns (545-547), then _OHLC_COLUMNS (548-550), then volume (551-552)

### Claim 20
- **Doc**: line 78: "Группировка — без columns, fallback" result is "dow | mean_gap" (group key + aggregate)
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:531-544` — fallback adds group_cols after date/time (542-544); for grouped results, DataFrame columns are [group_key, aggregate_result], so fallback ordering naturally produces group key first

### Claim 21
- **Doc**: line 11: "Идентификация → ответ → контекст" as explanation for ordering
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:502-511` — docstring comment: "Map columns before OHLC: derived data is more relevant than raw candles" matches the doc's "ответ → контекст" (answer before context) principle

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 21 |
| OUTDATED | 0 |
| WRONG | 0 |
| MISSING | 0 |
| UNVERIFIABLE | 0 |
| **Total** | **21** |
| **Accuracy** | **100%** |

All claims verified against actual code. Documentation is fully accurate.
