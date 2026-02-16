# Audit: column-ordering.md

Date: 2026-02-16

## Claims

### Claim 1
- **Doc**: line 9: "Interpreter показывает ровно эти колонки в указанном порядке"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:525-529` — `if columns: cols = [c for c in columns if c in df.columns]; if cols: return df[cols]` filters and orders columns exactly as specified in the columns array

### Claim 2
- **Doc**: line 11: "Правило порядка в промпте: `date/time first, then answer columns (from map), then supporting context (close, volume)`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:35` — prompt states "Order: date/time first, then answer columns (from map), then supporting context (close, volume)"

### Claim 3
- **Doc**: line 13: "`columns` к ним не применяется" (columns applies only to table results, not scalar/grouped)
- **Verdict**: WRONG
- **Evidence**: `barb/interpreter.py:525-529` — `_prepare_for_output()` applies columns filter to ALL DataFrames, including grouped results. The code does not check `query.get("group_by")` before applying columns projection. Grouped results ARE DataFrames and go through the same projection logic.
- **Fix**: change "Scalar и grouped результаты управляют своими колонками — `columns` к ним не применяется" → "Scalar results ignore columns (not DataFrames). Grouped DataFrames can use columns projection."

### Claim 4
- **Doc**: line 20: "date — всегда первая"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:538-539` — `if "date" in df.columns: ordered.append("date")` — date is first in ordered list

### Claim 5
- **Doc**: line 21: "time — только для intraday"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:540-541` + line 50 — `if "time" in df.columns: ordered.append("time")` after checking `timeframe in _INTRADAY_TIMEFRAMES` at line 520

### Claim 6
- **Doc**: line 22: "group keys — если есть group_by"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:542-544` — `for col in group_cols: if col in df.columns and col not in ordered: ordered.append(col)`

### Claim 7
- **Doc**: line 23: "calculated — колонки из map, в порядке объявления"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:532` + `545-547` — `map_columns = list(query.get("map", {}).keys())` preserves declaration order (dict keys maintain insertion order in Python 3.7+), then appended to ordered list

### Claim 8
- **Doc**: line 24: "OHLC — open, high, low, close"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:53` + `548-550` — `_OHLC_COLUMNS = ["open", "high", "low", "close"]` used in loop `for col in _OHLC_COLUMNS`

### Claim 9
- **Doc**: line 25: "volume"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:551-552` — `if "volume" in df.columns: ordered.append("volume")`

### Claim 10
- **Doc**: line 26: "remaining — все остальные"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:553-555` — `for col in df.columns: if col not in ordered: ordered.append(col)`

### Claim 11
- **Doc**: line 35: "1m, 5m, 15m, 30m, 1h, 2h, 4h — date + time"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:50` — `_INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}` checked at line 520 to add time column

### Claim 12
- **Doc**: line 36: "daily, weekly, monthly, quarterly, yearly — только date"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:520-521` — `if timeframe in _INTRADAY_TIMEFRAMES: df["time"] = ...` — time only added for intraday, daily+ gets date only

### Claim 13
- **Doc**: line 50: "Результат: `date | chg | close` — ответ (chg) перед контекстом (close)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:525-529` — columns=["date", "chg", "close"] would filter df to exactly these columns in this order via projection mode

### Claim 14
- **Doc**: line 62: "Результат: `date | close | sma50 | sma200` — `cross` использовался для фильтра, но скрыт"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:525-529` — columns array excludes "cross", so it won't appear in output even though it exists in the DataFrame

### Claim 15
- **Doc**: line 70: "Результат: `date | chg | open | high | low | close | volume` — fallback ordering"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:531-557` — without columns, fallback applies: date (538-539), map columns like chg (545-547), OHLC (548-550), volume (551-552)

### Claim 16
- **Doc**: line 78: "Результат: `dow | mean_gap` — управляется group_by логикой"
- **Verdict**: WRONG
- **Evidence**: `barb/interpreter.py:525-529` — columns projection is applied to ALL DataFrames including grouped ones. This statement contradicts the code. If columns were passed, it would override the "natural" group_by output. The doc implies grouped results bypass columns, but they don't.
- **Fix**: change "управляется group_by логикой" → "без columns — fallback порядок (group key первым, затем aggregate). С columns — применяется projection."

### Claim 17
- **Doc**: line 84-86: "1. Split timestamp → date/time, 2. Если `columns` есть → projection, 3. Иначе → fallback ordering"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:516-557` — code executes: split timestamp (516-522), check columns (525-529), fallback (531-557)

### Claim 18
- **Doc**: line 88: "Вызывается в `_build_response()` перед сериализацией"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:616` + `621` — `prepared = _prepare_for_output(...)` called before `_serialize_records(prepared.to_dict("records"))`

### Claim 19
- **Doc**: line 92: "Фронтенд использует порядок из первой строки результата, с fallback на `Object.keys(rows[0])`"
- **Verdict**: WRONG
- **Evidence**: `front/src/components/panels/data-panel.tsx:62` — `const keys = columnOrder ?? Object.keys(rows[0])` — frontend uses `columnOrder` (from backend's columns field) first, then fallback to Object.keys. The doc states "порядок из первой строки" which is Object.keys, but misses that there's a HIGHER priority source: the columns array from backend.
- **Fix**: change "Фронтенд использует порядок из первой строки результата, с fallback на `Object.keys(rows[0])`" → "Фронтенд использует `columns` из DataBlock (backend prepared columns), fallback на `Object.keys(rows[0])` для старых данных"

### Claim 20
- **Doc**: line 92: "PostgreSQL JSONB не сохраняет порядок ключей"
- **Verdict**: UNVERIFIABLE
- **Evidence**: This is a statement about PostgreSQL behavior, not verifiable from codebase alone. However, the code's handling (assistant/chat.py:202-204 extracting columns from first row) suggests this is true.

### Claim 21
- **Doc**: line 96: "`_PRESERVE_PRECISION` — OHLCV колонки"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:56` — `_PRESERVE_PRECISION = {"open", "high", "low", "close", "volume"}`

### Claim 22
- **Doc**: line 96: "остальные float колонки округляются до `CALCULATED_PRECISION = 4`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:59` — `CALCULATED_PRECISION = 4` and lines 577-585 round floats not in _PRESERVE_PRECISION to CALCULATED_PRECISION

### Claim 23
- **Doc**: line 98: "Обрабатывается в `_serialize_records()` при конвертации DataFrame → JSON"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:560-589` — `_serialize_records()` function applies precision rules when converting records to JSON

### Claim 24
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/chat.py:202-204` — backend extracts `columns = list(ui_data[0].keys())` from serialized records to send to frontend. This is a critical implementation detail for preserving column order across JSONB serialization that's not documented.
- **Fix**: add to "Реализация" section: "Backend extracts column order from serialized records (chat.py:202-204) and sends as `columns` field to frontend, preserving order despite JSONB limitations."

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 18 |
| OUTDATED | 0 |
| WRONG | 3 |
| MISSING | 1 |
| UNVERIFIABLE | 1 |
| **Total** | **23** |
| **Accuracy** | **78%** |

Accuracy = 18 / 23 × 100 = 78%

## Key Issues

1. **Claim 3 & 16**: Doc incorrectly states that grouped results ignore `columns` projection, but the code applies it to all DataFrames
2. **Claim 19**: Doc misses that frontend prioritizes backend's `columns` field over Object.keys
3. **Claim 24**: Missing documentation about how backend preserves column order through JSONB by extracting keys from serialized records
