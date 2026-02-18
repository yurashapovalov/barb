# Audit: query-engine.md

Date: 2026-02-18

## Claims

### Claim 1
- **Doc**: line 5: "Запрос — плоский JSON. Каждое поле — шаг пайплайна. Порядок выполнения фиксированный, не зависит от порядка полей в JSON."
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:3-6` — docstring: "9-step pipeline, fixed execution order regardless of JSON key order: session → period → from → map → where → group_by → select → sort → limit"

### Claim 2
- **Doc**: line 12: "1. session — фильтр по торговой сессии (RTH, ETH)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:114` — `# 1. SESSION — filter by time of day`; `barb/interpreter.py:220` — `def filter_session(df, session, sessions)`

### Claim 3
- **Doc**: line 13: "2. period — фильтр по периоду (YYYY, YYYY-MM, YYYY-MM-DD, start:end где каждая часть любого формата, last_year, last_month, last_week)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:243-244` — `_RELATIVE_PERIODS = {"last_year", "last_month", "last_week"}` and `_PERIOD_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")`; `barb/interpreter.py:253` — range parsed with `":"` split

### Claim 4
- **Doc**: line 14: "3. from — ресемплинг таймфрейма (1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:18-31` — `TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h", "daily", "weekly", "monthly", "quarterly", "yearly"}` — exact match

### Claim 5
- **Doc**: line 15: "4. map — вычисляемые колонки {\"name\": \"expression\"}"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:133-134` — `if query.get("map"): df = compute_map(df, query["map"])`; `barb/interpreter.py:319` — `def compute_map(df, map_config: dict)`

### Claim 6
- **Doc**: line 16: "5. where — фильтр строк по условию (expression)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:137-138` — `if query.get("where"): df = filter_where(df, query["where"])`

### Claim 7
- **Doc**: line 17: "6. group_by — группировка (по колонке из map)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:143` — `group_by = query.get("group_by")`; `barb/interpreter.py:149-151` — `if group_by: select = ...; result_df = _group_aggregate(df, group_by, select)`

### Claim 8
- **Doc**: line 18: "7. select — агрегация (\"count()\", \"mean(col)\", [\"sum(x)\", \"max(y)\"])"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:152-154` — `elif select_raw: select = _normalize_select(select_raw); result_df = _aggregate(df, select)`; `barb/interpreter.py:174-177` — `_normalize_select` handles comma-separated strings and list forms

### Claim 9
- **Doc**: line 19: "8. sort — сортировка (\"column desc\" или \"column asc\", по имени колонки из map, не выражению)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:473-496` — `def sort_df(df, sort)` splits on space, checks column name, raises error if not found; no expression evaluation

### Claim 10
- **Doc**: line 20: "9. limit — ограничение количества строк"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:163-164` — `if query.get("limit") and isinstance(result_df, pd.DataFrame): result_df = result_df.head(query["limit"])`

### Claim 11
- **Doc**: line 22: "Projection (columns) → Результат (summary для модели + table для UI)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:499-557` — `_prepare_for_output(df, query)` applies `columns` projection post-pipeline; `barb/interpreter.py:101-102` — return dict contains `summary` and `table`

### Claim 12
- **Doc**: line 28: "`execute(query, df, sessions)` прогоняет по 9 шагам"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:92` — `def execute(query: dict, df: pd.DataFrame, sessions: dict) -> dict:`

### Claim 13
- **Doc**: lines 29-35: "`execute()` возвращает dict с: `summary`, `table`, `source_rows`, `source_row_count`, `metadata`, `query`, `chart`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:100-102` — docstring return annotation: `{"summary": ..., "table": [...] | None, "source_rows": ..., "source_row_count": ..., "metadata": {...}, "query": query, "chart": ...}`; `barb/interpreter.py:645-653` — actual return for DataFrame path confirms all 7 keys

### Claim 14
- **Doc**: line 35: "`chart` — hint для фронтенда (`{category, value}`, только для grouped DataFrame результатов; ключ отсутствует в scalar/dict ответах)"
- **Verdict**: WRONG
- **Evidence**: `barb/interpreter.py:635` — `chart = None` is set before the grouped check; `barb/interpreter.py:652` — `"chart": chart` is always included in the DataFrame return (grouped AND non-grouped), not only grouped results. For scalar (line 680-687) and dict (line 662-669) results, the key IS absent — that part is correct. But the key is present (as `None`) for non-grouped DataFrame results too, not only grouped.
- **Fix**: Change "только для grouped DataFrame результатов" → "всегда присутствует в DataFrame результатах (None когда нет group_by); ключ отсутствует в scalar/dict ответах"

### Claim 15
- **Doc**: line 38: "**table**: `{type, rows, columns, stats:{col:{min,max,mean}}, first:{date,..}, last:{date,..}}`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:699-703` — `summary = {"type": "grouped" if is_grouped else "table", "rows": len(table), "columns": list(df.columns)}`; lines 710-719 — `stats` dict with `min`, `max`, `mean`; lines 722-733 — `first` and `last` rows

### Claim 16
- **Doc**: line 39: "**grouped**: table + `{by, min_row, max_row}`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:705-707` — `if is_grouped: summary["by"] = ...`; lines 736-744 — `summary["min_row"]` and `summary["max_row"]` added for grouped results

### Claim 17
- **Doc**: line 40: "**scalar**: `{type: \"scalar\", value, rows_scanned}`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:675-678` — `summary = {"type": "scalar", "value": result, "rows_scanned": source_row_count or rows}`

### Claim 18
- **Doc**: line 41: "**dict**: `{type: \"dict\", values, rows_scanned}`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:657-660` — `summary = {"type": "dict", "values": result, "rows_scanned": source_row_count or rows}`

### Claim 19
- **Doc**: line 43: "`columns` — массив имён колонок для projection. Не шаг пайплайна, а post-processing: после всех 9 шагов, перед сериализацией, `_prepare_for_output()` фильтрует и упорядочивает колонки по `columns`."
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:499-529` — `_prepare_for_output(df, query)` is called after all 9 steps; lines 524-529 — `columns = query.get("columns"); if columns: cols = [c for c in columns if c in df.columns]; if cols: return df[cols]`

### Claim 20
- **Doc**: line 45: "Валидирует входные данные — неизвестные поля, невалидные таймфреймы, невалидный limit, некорректный map, формат columns."
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:184-214` — `_validate(query)` checks unknown fields (line 186-192), invalid timeframe (line 194-200), invalid limit (line 202-207), invalid map type (line 209-213); `barb/validation.py:104-113` — columns format validated in `validate_expressions`

### Claim 21
- **Doc**: line 48: "Пре-валидация выражений до запуска пайплайна. Без DataFrame — чистый AST-анализ."
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:1-6` — "Catches syntax errors, unknown functions, and unsupported operators across ALL fields at once — before the pipeline executes. No DataFrame required."; `barb/interpreter.py:108` — `validate_expressions(query)` called before step 1

### Claim 22
- **Doc**: line 49-50: "Проверяет: Синтаксис всех выражений (map, where, select)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:47-73` — map expressions checked lines 48-61, where expression lines 64-66, select lines 68-73

### Claim 23
- **Doc**: line 51: "Неизвестные функции"
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:152-166` — `_walk_ast` checks function names against `_KNOWN_FUNCTIONS` and appends error if not found

### Claim 24
- **Doc**: line 52: "Неподдерживаемые операторы и вызовы методов (`a.upper()` — запрещено)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:167-174` — method calls (non-Name func) caught and appended as error; `barb/validation.py:179-188` — unsupported binary operators checked

### Claim 25
- **Doc**: line 53: "`=` вместо `==` (частая ошибка LLM)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:29-30` — `_LONE_EQUALS_RE = re.compile(r"(?<![=!<>])=(?!=)")`; `barb/validation.py:121-131` — lone `=` check with hint message

### Claim 26
- **Doc**: line 54: "Функции в `group_by` (LLM иногда пишет `group_by: \"dayofweek()\"` вместо создания колонки в map)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:75-101` — checks if `group_by` string or list items contain `"("` and appends descriptive error with hint

### Claim 27
- **Doc**: line 55: "Формат агрегатных выражений в group_by контексте (должно быть `func(col)` или `count()`)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:254-285` — `_check_group_select` validates against `_AGG_EXPR_RE = re.compile(r"^(\w+)\((\w+)?\)$")` and checks against `AGGREGATE_FUNCS`

### Claim 28
- **Doc**: line 56: "`columns` — должен быть массив строк (если указан)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:104-113` — `if columns is not None: if not isinstance(columns, list) or any(not isinstance(c, str) for c in columns): errors.append(...)`

### Claim 29
- **Doc**: line 57: "Собирает все ошибки разом — `ValidationError(errors: list[dict])`."
- **Verdict**: ACCURATE
- **Evidence**: `barb/validation.py:20-26` — `class ValidationError(Exception): def __init__(self, errors: list[dict]):`; `barb/validation.py:45` — `errors: list[dict] = []` accumulated throughout; `barb/validation.py:115-116` — `if errors: raise ValidationError(errors)`

### Claim 30
- **Doc**: line 60: "Парсер и вычислитель выражений. Безопасный — никакого eval/exec. Строит AST через `ast.parse()`, вычисляет рекурсивно на DataFrame."
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:99-106` — `parsed_expr = _preprocess_keywords(expr); tree = ast.parse(parsed_expr, mode="eval"); return _eval_node(tree.body, df, functions)` — no eval/exec, pure AST

### Claim 31
- **Doc**: line 61: "Арифметику: `+`, `-`, `*`, `/`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:67-72` — `_BINARY_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}` — exactly these four

### Claim 32
- **Doc**: line 62: "Сравнения: `>`, `<`, `>=`, `<=`, `==`, `!=`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:74-81` — `_COMPARE_OPS = {ast.Gt, ast.Lt, ast.GtE, ast.LtE, ast.Eq, ast.NotEq}` — exactly these six

### Claim 33
- **Doc**: line 63: "Булеву логику: `and`, `or`, `not`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:181-193` — BoolOp handles `ast.And` and `ast.Or`; `barb/expressions.py:143-144` — UnaryOp handles `ast.Not`

### Claim 34
- **Doc**: line 64: "Membership: `in [1, 2, 3]`, `not in [4, 5]`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:153-167` — `ast.In` and `ast.NotIn` handled in Compare node, using `.isin()` for Series

### Claim 35
- **Doc**: line 65: "Функции: `prev()`, `rolling_mean()`, `dayofweek()`, etc."
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:196-218` — ast.Call node handled, dispatches to `functions` dict which includes `prev`, `rolling_mean`, `dayofweek`

### Claim 36
- **Doc**: line 66: "Автоконвертация дат: `date() >= '2024-03-15'` (строки автоматически парсятся в `datetime.date`)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/expressions.py:36-46` — `_coerce_for_date_comparison(left, right)` converts string to date when comparing with date Series; `barb/expressions.py:173-174` — called in Compare evaluation

### Claim 37
- **Doc**: line 69: "Реестр 106 функций в 12 модулях."
- **Verdict**: ACCURATE
- **Evidence**: Running `len(FUNCTIONS)` returns 106; `barb/functions/__init__.py:7-51` imports from 12 modules (aggregate, convenience, core, cumulative, lag, oscillators, pattern, time, trend, volatility, volume, window)

### Claim 38
- **Doc**: line 69: "Каждый модуль экспортирует `*_FUNCTIONS`, `*_SIGNATURES`, `*_DESCRIPTIONS`."
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/__init__.py:7-51` — each import includes the three dicts (e.g., `AGGREGATE_FUNCTIONS, AGGREGATE_SIGNATURES, AGGREGATE_DESCRIPTIONS`); confirmed in all 12 module files

### Claim 39
- **Doc**: line 69: "`__init__.py` объединяет в `FUNCTIONS`, `SIGNATURES`, `DESCRIPTIONS`."
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/__init__.py:53-96` — `FUNCTIONS = {**CORE_FUNCTIONS, ...}`, `SIGNATURES = {**CORE_SIGNATURES, ...}`, `DESCRIPTIONS = {**CORE_DESCRIPTIONS, ...}`

### Claim 40
- **Doc**: line 72: "**core** (6) — `abs`, `log`, `sqrt`, `sign`, `round`, `if`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/core.py:14-21` — `CORE_FUNCTIONS` has exactly 6 keys: `abs`, `log`, `sqrt`, `sign`, `round`, `if`

### Claim 41
- **Doc**: line 73: "**lag** (2) — `prev`, `next`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/lag.py:3-6` — `LAG_FUNCTIONS = {"prev": ..., "next": ...}` — exactly 2 functions

### Claim 42
- **Doc**: line 74: "**window** (12) — `sma`, `ema`, `wma`, `hma`, `rma`, `vwma`, `rolling_mean`, `rolling_sum`, `rolling_max`, `rolling_min`, `rolling_std`, `rolling_count`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/window.py:52-65` — `WINDOW_FUNCTIONS` has exactly 12 keys matching the listed names

### Claim 43
- **Doc**: line 75: "**cumulative** (3) — `cumsum`, `cummax`, `cummin`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/cumulative.py:3-7` — `CUMULATIVE_FUNCTIONS = {"cummax": ..., "cummin": ..., "cumsum": ...}` — exactly 3

### Claim 44
- **Doc**: line 76: "**pattern** (8) — `streak`, `bars_since`, `rank`, `rising`, `falling`, `valuewhen`, `pivothigh`, `pivotlow`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/pattern.py:99-108` — `PATTERN_FUNCTIONS` has exactly 8 keys matching the listed names

### Claim 45
- **Doc**: line 77: "**aggregate** (10) — `mean`, `sum`, `count`, `max`, `min`, `std`, `median`, `percentile`, `correlation`, `last`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/aggregate.py:5-16` — `AGGREGATE_FUNCTIONS` has exactly 10 keys matching the listed names

### Claim 46
- **Doc**: line 78: "**time** (10) — `dayofweek`, `dayname`, `hour`, `minute`, `month`, `year`, `date`, `monthname`, `day`, `quarter`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/time.py:5-16` — `TIME_FUNCTIONS` has exactly 10 keys matching the listed names

### Claim 47
- **Doc**: line 79: "**convenience** (19) — `change`, `change_pct`, `gap`, `gap_pct`, `range`, `range_pct`, `body`, `body_pct`, `upper_wick`, `lower_wick`, `midpoint`, `typical_price`, `green`, `red`, `doji`, `inside_bar`, `outside_bar`, `crossover`, `crossunder`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/convenience.py:100-123` — `CONVENIENCE_FUNCTIONS` has exactly 19 keys matching all listed names

### Claim 48
- **Doc**: line 80: "**oscillators** (8) — `rsi`, `stoch_k`, `stoch_d`, `cci`, `williams_r`, `mfi`, `momentum`, `roc`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/oscillators.py:85-94` — `OSCILLATOR_FUNCTIONS` has exactly 8 keys matching the listed names

### Claim 49
- **Doc**: line 81: "**volatility** (14) — `tr`, `atr`, `natr`, `bbands_upper`, `bbands_middle`, `bbands_lower`, `bbands_width`, `bbands_pctb`, `donchian_upper`, `donchian_lower`, `kc_upper`, `kc_middle`, `kc_lower`, `kc_width`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/volatility.py:114-129` — `VOLATILITY_FUNCTIONS` has exactly 14 keys matching the listed names

### Claim 50
- **Doc**: line 82: "**trend** (9) — `macd`, `macd_signal`, `macd_hist`, `adx`, `plus_di`, `minus_di`, `sar`, `supertrend`, `supertrend_dir`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/trend.py:219-229` — `TREND_FUNCTIONS` has exactly 9 keys matching the listed names

### Claim 51
- **Doc**: line 83: "**volume** (5) — `obv`, `ad_line`, `vwap_day`, `volume_sma`, `volume_ratio`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/functions/volume.py:53-59` — `VOLUME_FUNCTIONS` has exactly 5 keys matching the listed names

### Claim 52
- **Doc**: line 86: "Загрузка Parquet файлов. `load_data(instrument, timeframe=\"1d\", asset_type=\"futures\")`."
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:12` — `def load_data(instrument: str, timeframe: str = "1d", asset_type: str = "futures") -> pd.DataFrame:`

### Claim 53
- **Doc**: line 86: "Два набора: `data/1d/futures/{symbol}.parquet` (дневные) и `data/1m/futures/{symbol}.parquet` (минутные)."
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:20` — `path = DATA_DIR / timeframe / asset_type / f"{instrument.upper()}.parquet"` — path structure matches both cases

### Claim 54
- **Doc**: line 86: "Кэшируется через `@lru_cache`."
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:11` — `@lru_cache` decorator on `load_data`

### Claim 55
- **Doc**: line 86: "Возвращает DataFrame с DatetimeIndex и колонками [open, high, low, close, volume]."
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:25-27` — `df = df.set_index("timestamp"); df = df[["open", "high", "low", "close", "volume"]]`

### Claim 56
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/functions/_smoothing.py` exists as an internal helper module providing `wilder_smooth` used by `rma`, `rsi`, `atr`, `adx`, and `supertrend`. The doc lists "12 modules" but `_smoothing.py` is a 13th file in the package (internal, not a registry module). The doc's "12 modules" count is correct since `_smoothing` exports no `*_FUNCTIONS` dict, but its existence and role is undocumented.
- **Fix**: Consider adding a note in the functions/ section: "_smoothing.py — internal helper, provides `wilder_smooth` for RSI/ATR/ADX matching"

### Claim 57
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:18-31` — `TIMEFRAMES` set is the single source of truth for valid `from` values. The `from` field defaults to `"1m"` when absent (`barb/interpreter.py:112` — `timeframe = query.get("from", "1m")`), but the doc does not mention this default.
- **Fix**: Add to the `from` step description: "default: `1m` when field is omitted"

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 53 |
| OUTDATED | 0 |
| WRONG | 1 |
| MISSING | 2 |
| UNVERIFIABLE | 0 |
| **Total** | **56** |
| **Accuracy** | **95%** |

Accuracy = 53 / 56 × 100 ≈ 95%
