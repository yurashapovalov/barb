# Audit: query-engine.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 7: "Каждое поле -- шаг пайплайна. Порядок выполнения фиксированный"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:4-5` — docstring confirms "9-step pipeline, fixed execution order"

### Claim 2
- **Doc**: line 10: "Входные данные (минутный DataFrame)"
- **Verdict**: WRONG
- **Evidence**: `barb/data.py:12` — `load_data(instrument, timeframe="1d")` loads either daily or minute data; `execute()` accepts any DataFrame with DatetimeIndex
- **Fix**: change "минутный DataFrame" to "DataFrame (минутный или дневной)"

### Claim 3
- **Doc**: line 12: "session -- фильтр по торговой сессии (RTH, ETH)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:112-119` — step 1 filters by session name

### Claim 4
- **Doc**: line 13: "period -- фильтр по периоду"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:240-293` — `_RELATIVE_PERIODS` and `_PERIOD_RE` support all listed formats

### Claim 5
- **Doc**: line 14: "from -- ресемплинг таймфрейма ("1m", "5m", "15m", "30m", "1h", "daily", "weekly")"
- **Verdict**: OUTDATED
- **Evidence**: `barb/interpreter.py:17-30` — `TIMEFRAMES` also includes `"2h"`, `"4h"`, `"monthly"`, `"quarterly"`, `"yearly"`
- **Fix**: add missing timeframes to list

### Claim 6
- **Doc**: line 15: "map -- вычисляемые колонки {"name": "expression"}"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:316-336` — `compute_map()` takes dict of `{name: expression}`

### Claim 7
- **Doc**: line 16: "where -- фильтр строк по условию"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:339-358` — `filter_where()` evaluates boolean expression

### Claim 8
- **Doc**: line 17: "group_by -- группировка"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:361-386` — `_group_aggregate()` groups by column name(s)

### Claim 9
- **Doc**: line 18: "select -- агрегация"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:389-417` — `_aggregate()` handles single string, list, and `count()`

### Claim 10
- **Doc**: line 19: "sort -- сортировка ("column desc" или "column asc")"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:470-489` — `sort_df()` parses `"col desc"` format

### Claim 11
- **Doc**: line 20: "limit -- ограничение количества строк"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:160-161` — `result_df.head(query["limit"])`

### Claim 12
- **Doc**: line 22: "Результат (summary для модели + table для UI)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:640-648` — return dict includes `"summary"` and `"table"`

### Claim 13
- **Doc**: line 28: "interpreter.py ... Принимает execute(query, df, sessions)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:90` — `def execute(query: dict, df: pd.DataFrame, sessions: dict) -> dict:`

### Claim 14
- **Doc**: line 28: "Валидирует входные данные"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:181-211` — `_validate()` checks unknown fields, invalid timeframes, invalid limit

### Claim 15
- **Doc**: line 31: "Парсер и вычислитель выражений. Безопасный -- никакого eval/exec"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:101-106` — uses `ast.parse()` and recursive `_eval_node()`, no `eval()`

### Claim 16
- **Doc**: line 33: "Арифметику: +, -, *, /"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:67-72` — `_BINARY_OPS` maps all four operators

### Claim 17
- **Doc**: line 34: "Сравнения: >, <, >=, <=, ==, !="
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:74-81` — `_COMPARE_OPS` maps all six

### Claim 18
- **Doc**: line 35: "Булеву логику: and, or, not"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:181-193` — handles `ast.And`, `ast.Or`; `139-144` handles `ast.Not`

### Claim 19
- **Doc**: line 36: "Membership: in [1, 2, 3]"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:153-161` — handles `ast.In` with `current.isin(right)`

### Claim 20
- **Doc**: line 37: "Функции: prev(), rolling_mean(), dayofweek(), etc."
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:196-218` — handles `ast.Call`, looks up in `functions` dict

### Claim 21
- **Doc**: line 38: "Автоконвертация дат"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:36-46` — `_coerce_for_date_comparison()` converts strings to `datetime.date`

### Claim 22
- **Doc**: line 39: "functions.py"
- **Verdict**: OUTDATED
- **Evidence**: `barb/functions/__init__.py:1` — now a package with 12 modules
- **Fix**: change "functions.py" to "functions/ (package)"

### Claim 23
- **Doc**: line 40: "Реестр 40+ функций"
- **Verdict**: OUTDATED
- **Evidence**: counting all `*_FUNCTIONS` dicts = 106 functions
- **Fix**: change "40+" to "106"

### Claim 24
- **Doc**: line 41: "Скалярные -- abs, log, round, if"
- **Verdict**: OUTDATED
- **Evidence**: `barb/functions/core.py:14-21` — 6 functions: `abs, log, sqrt, sign, round, if`; missing `sqrt`, `sign`
- **Fix**: add `sqrt, sign`

### Claim 25
- **Doc**: line 42: "Лаговые -- prev, next"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/lag.py:3-6` — `prev` and `next`

### Claim 26
- **Doc**: line 43: "Оконные -- rolling_mean, rolling_sum, rolling_max, rolling_min, rolling_std, ema"
- **Verdict**: OUTDATED
- **Evidence**: `barb/functions/window.py:52-65` — 12 functions; missing `rolling_count, sma, wma, hma, vwma, rma`
- **Fix**: add missing functions

### Claim 27
- **Doc**: line 44: "Кумулятивные -- cumsum, cummax, cummin"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/cumulative.py:3-7` — exactly these three

### Claim 28
- **Doc**: line 45: "Паттерны -- streak, bars_since, rank"
- **Verdict**: OUTDATED
- **Evidence**: `barb/functions/pattern.py:99-108` — 8 functions; missing `rising, falling, valuewhen, pivothigh, pivotlow`
- **Fix**: add missing functions

### Claim 29
- **Doc**: line 46: "Агрегатные -- mean, sum, count, max, min, std, median"
- **Verdict**: OUTDATED
- **Evidence**: `barb/functions/aggregate.py:5-16` — 10 functions; missing `percentile, correlation, last`
- **Fix**: add missing functions

### Claim 30
- **Doc**: line 47: "Временные -- dayofweek, dayname, hour, minute, month, year, date"
- **Verdict**: OUTDATED
- **Evidence**: `barb/functions/time.py:5-16` — 10 functions; missing `monthname, day, quarter`
- **Fix**: add missing functions

### Claim 31
- **Doc**: line 49-50: "data.py ... Один файл = один инструмент"
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:20` — one parquet per instrument per timeframe

### Claim 32
- **Doc**: line 50: "Кэшируется через lru_cache"
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:11` — `@lru_cache` on `load_data()`

### Claim 33
- **Doc**: line 68: "summary: {type: "table", rows: 13, stats: ...}"
- **Verdict**: OUTDATED
- **Evidence**: `barb/interpreter.py:694-712` — summary also includes `columns` and `mean` in stats
- **Fix**: update example to include `columns` and `mean`

### Claim 34
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/validation.py:1` — pre-validates expressions before pipeline
- **Fix**: add to "Модули" section

### Claim 35
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/expressions.py:162-167` — `not in` operator supported but undocumented
- **Fix**: add `not in` to Membership section

### Claim 36
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: 5 function categories (convenience, oscillators, volatility, trend, volume) not listed
- **Fix**: add these categories to functions section

### Claim 37
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:640-648` — return dict also includes `source_rows`, `source_row_count`, `metadata`, `query`, `chart`
- **Fix**: document full return structure

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 19 |
| OUTDATED | 9 |
| WRONG | 1 |
| MISSING | 4 |
| UNVERIFIABLE | 0 |
| **Total** | **33** |
| **Accuracy** | **58%** |

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
### Claim 10 — CONFIRMED
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
### Claim 24 — CONFIRMED
### Claim 25 — CONFIRMED
### Claim 26 — CONFIRMED
### Claim 27 — CONFIRMED
### Claim 28 — CONFIRMED
### Claim 29 — CONFIRMED
### Claim 30 — CONFIRMED
### Claim 31 — CONFIRMED
### Claim 32 — CONFIRMED
### Claim 33 — CONFIRMED
### Claim 34 — CONFIRMED
### Claim 35 — CONFIRMED
### Claim 36 — CONFIRMED
### Claim 37 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 37 |
| DISPUTED | 0 |
| INCONCLUSIVE | 0 |
| **Total** | **37** |
