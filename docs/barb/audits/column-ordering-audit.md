# Audit: column-ordering.md

Date: 2026-02-16

## Claims

### Claim 1
- **Doc**: line 7: "Модель указывает `columns`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:72` — `"columns"` in `_VALID_FIELDS`; `assistant/tools/__init__.py:106-109` — `columns` in input schema

### Claim 2
- **Doc**: line 9: "Interpreter показывает ровно эти колонки в указанном порядке"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:526-529` — `cols = [c for c in columns if c in df.columns]`, then `return df[cols]` preserves exact order from columns array

### Claim 3
- **Doc**: line 11: "Правило порядка в промпте: `date/time first, then answer columns (from map), then supporting context (close, volume)`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:35` — "Order: date/time first, then answer columns (from map), then supporting context (close, volume)."

### Claim 4
- **Doc**: line 13: "для grouped результатов колонки из `columns` обычно не совпадают с реальными (group key + aggregate) → fallback"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:620-621` — grouped results are DataFrames and go through `_prepare_for_output()`, if columns don't match actual DataFrame columns (group keys + aggregates), projection filter `[c for c in columns if c in df.columns]` at line 527 causes fallback to ordered list at lines 536-556

### Claim 5
- **Doc**: line 13: "Промпт говорит: 'Omit columns for scalar/grouped results.'"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:36` — "Omit columns for scalar/grouped results (they manage their own output)."

### Claim 6
- **Doc**: line 17-27: "Fallback ordering: 1. date 2. time 3. group keys 4. calculated 5. OHLC 6. volume 7. remaining"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:536-556` — fallback logic: date (538-539), time (540-541), group keys (542-544), map columns (545-547), OHLC (548-550), volume (551-552), remaining (553-555)

### Claim 7
- **Doc**: line 31-32: "`timestamp` разбивается на `date` и `time`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:517-522` — `ts = pd.to_datetime(df["timestamp"])`, `df["date"] = ts.dt.strftime("%Y-%m-%d")`, conditionally creates `time` for intraday

### Claim 8
- **Doc**: line 35: "Timeframe 1m, 5m, 15m, 30m, 1h, 2h, 4h → `date` + `time`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:50` — `_INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}`; line 520-521: time created `if timeframe in _INTRADAY_TIMEFRAMES`

### Claim 9
- **Doc**: line 36: "daily, weekly, monthly, quarterly, yearly → только `date`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:520-521` — time only created for `_INTRADAY_TIMEFRAMES`, daily+ excluded implicitly

### Claim 10
- **Doc**: line 38: "Модель пишет `\"date\"` в `columns` — interpreter знает как его создать из timestamp"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:482-484` — `"date" is created later in _prepare_for_output(); alias to timestamp` handles date in sort/where before it exists; line 519: date created from timestamp in `_prepare_for_output()`

### Claim 11
- **Doc**: line 45-47: "Projection example with columns: ['date', 'chg', 'close']"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:526-529` — projection applies columns order exactly as specified

### Claim 12
- **Doc**: line 54-62: "Projection can hide helper columns like 'cross'"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:527` — `cols = [c for c in columns if c in df.columns]` only includes columns listed in array, helper columns not listed are excluded

### Claim 13
- **Doc**: line 66-70: "Fallback example without columns → `date | chg | open | high | low | close | volume`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:536-556` — fallback ordering: date first, then map columns (chg), then OHLC, then volume

### Claim 14
- **Doc**: line 74-78: "Группировка — columns не применяется"
- **Verdict**: WRONG
- **Evidence**: `barb/interpreter.py:620-621` — grouped results go through `_prepare_for_output(result, query)` which checks for `columns` at line 525, projection applies to ALL DataFrames including grouped
- **Fix**: change "columns не применяется" → "columns применяется технически, но обычно не совпадают с реальными колонками и вызывают fallback"

### Claim 15
- **Doc**: line 82-86: "`_prepare_for_output()`: 1. Split timestamp → date/time 2. Если `columns` есть → projection 3. Иначе → fallback ordering"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:499-557` — function performs: timestamp split (517-522), projection if columns exists (524-529), fallback ordering (531-556)

### Claim 16
- **Doc**: line 88: "Вызывается в `_build_response()` перед сериализацией"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:616` — `prepared = _prepare_for_output(source_df, query)` before `_serialize_records()`; line 621: `prepared = _prepare_for_output(result, query)` before serialization

### Claim 17
- **Doc**: line 92: "PostgreSQL JSONB не сохраняет порядок ключей"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:201` — comment: "Column order from _order_columns() — JSONB doesn't preserve key order"

### Claim 18
- **Doc**: line 92: "Бэкенд (`assistant/chat.py`) извлекает порядок колонок из сериализованных записей и передаёт как `columns` в data_block"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:202-209` — `columns = list(ui_data[0].keys()) if isinstance(ui_data, list) and ui_data else None`, then `"columns": columns` in block

### Claim 19
- **Doc**: line 92: "Фронтенд (`data-panel.tsx`) использует `columnOrder ?? Object.keys(rows[0])`"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/panels/data-panel.tsx:62` — `const keys = columnOrder ?? Object.keys(rows[0]);` (parameter is named `columnOrder` but receives `data.columns` at line 107)

### Claim 20
- **Doc**: line 96: "OHLCV колонки (`_PRESERVE_PRECISION`) сохраняют оригинальную точность"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:56` — `_PRESERVE_PRECISION = {"open", "high", "low", "close", "volume"}`; lines 577-578, 582-583: values in `_PRESERVE_PRECISION` are not rounded

### Claim 21
- **Doc**: line 96: "Все остальные float колонки округляются до `CALCULATED_PRECISION = 4`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:59` — `CALCULATED_PRECISION = 4`; line 580: `round(v, CALCULATED_PRECISION)` for non-preserved floats; line 585: same for direct floats

### Claim 22
- **Doc**: line 98: "Обрабатывается в `_serialize_records()` при конвертации DataFrame → JSON"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:560-589` — `_serialize_records()` converts records to JSON-serializable format with precision handling at lines 577-585

### Claim 23
- **Doc**: line 11: "Идентификация → ответ → контекст"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:35` — ordering rule places date/time (identification) first, then answer columns from map, then supporting context (close, volume)

### Claim 24
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:502-511` — docstring mentions "Map columns before OHLC: derived data is more relevant than raw candles" — design rationale not explained in doc
- **Fix**: add to section "Fallback ordering" explaining why calculated columns come before OHLC

### Claim 25
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/validation.py:103-111` — columns validation: must be list of strings, raises QueryError if invalid
- **Fix**: add to section "Реализация" mentioning validation in `barb/validation.py`

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 23 |
| OUTDATED | 0 |
| WRONG | 1 |
| MISSING | 2 |
| UNVERIFIABLE | 0 |
| **Total** | **26** |
| **Accuracy** | **88%** |

Accuracy = ACCURATE / Total × 100 = 23 / 26 × 100 = 88%
