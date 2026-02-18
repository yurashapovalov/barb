# Audit: result-format.md

Date: 2026-02-18

## Claims

### Claim 1
- **Doc**: line 9: "UI получает: ПОЛНЫЕ данные (table / source_rows)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:136-142` — `run_query` returns `"table": result.get("table")` and `"source_rows": result.get("source_rows")` which flow to UI via `data_block` SSE event

### Claim 2
- **Doc**: line 10: "Модель получает: МИНИМУМ для комментария (summary)"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:137` — `"model_response": _format_summary_for_model(summary)` sends only the compact string to the model

### Claim 3
- **Doc**: lines 17-30: data flow diagram listing SSE events `text_delta`, `tool_start`, `tool_end`, `data_block`, `done` from Chat, and `title_update`, `persist`, `error` from API
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:95` — yields `text_delta`; `chat.py:135-141` — yields `tool_start`; `chat.py:163-169` — yields `tool_end`; `chat.py:187` — yields `data_block`; `chat.py:229` — yields `done`; `api/main.py:686` — yields `title_update`; `api/main.py:724` — yields `persist`; `api/main.py:701` — yields `error`

### Claim 4
- **Doc**: line 34: "`barb/interpreter.py` → `execute()` → `_build_response()`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:166` — `return _build_response(result_df, query, rows_after_filter, session_name, timeframe, warnings, source_df)`

### Claim 5
- **Doc**: lines 39-58: interpreter DataFrame result includes keys `summary`, `table`, `source_rows`, `source_row_count`, `chart`, `metadata`, `query`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:645-653` — `return {"summary": summary, "table": table, "source_rows": source_rows, "source_row_count": source_row_count, "metadata": metadata, "query": query, "chart": chart}`

### Claim 6
- **Doc**: line 41: `"type": "table"  # или "grouped"` inside `summary`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:700` — `"type": "grouped" if is_grouped else "table"`

### Claim 7
- **Doc**: line 43: `"columns": ["open", "high", "low", "close", "volume", "change_pct"]` inside `summary`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:702` — `"columns": list(df.columns)` — columns come from the result DataFrame

### Claim 8
- **Doc**: line 44: `"stats": {"change_pct": {"min": -5.06, "max": -2.51, "mean": -3.27}}` inside `summary`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:713-718` — stats dict contains `{"min": ..., "max": ..., "mean": ...}` for each column in `summary_columns`

### Claim 9
- **Doc**: lines 45-46: `"first"` and `"last"` inside `summary` with date and map columns
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:723-733` — `first_last_cols = ["date", "time"] + map_columns`, then `summary["first"] = first_row` and `summary["last"] = last_row`

### Claim 10
- **Doc**: lines 48-50: grouped summary adds `"by"`, `"min_row"`, `"max_row"`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:706-707` — `summary["by"] = group_by`; `barb/interpreter.py:743-744` — `summary["min_row"]` and `summary["max_row"]`

### Claim 11
- **Doc**: line 52: `"table": [...]  # полные данные для UI`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:621-622` — `prepared = _prepare_for_output(result, query)` then `table = _serialize_records(prepared.to_dict("records"))`

### Claim 12
- **Doc**: line 53: `"source_rows": [...]  # строки до агрегации (если select)`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:611` — `has_aggregation = query.get("select") is not None`; `barb/interpreter.py:614-617` — source_rows populated only when `has_aggregation` is True

### Claim 13
- **Doc**: line 55: `"chart": {"category": "dow", "value": "mean_gap"}  # только grouped (None для table; отсутствует для scalar/dict)`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:635` — `chart = None` initialized for table; `barb/interpreter.py:636-643` — chart set to dict only when `is_grouped`; `barb/interpreter.py:662-668` — dict result has no `chart` key; `barb/interpreter.py:680-686` — scalar result has no `chart` key

### Claim 14
- **Doc**: line 56: `"metadata": {"rows": 80, "session": "RTH", "from": "daily", "warnings": []}`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:594-599` — `metadata = {"rows": rows, "session": session, "from": timeframe, "warnings": warnings}`

### Claim 15
- **Doc**: lines 63-70: scalar result structure `{"summary": {"type": "scalar", "value": 65, "rows_scanned": 500}, "table": None, "source_rows": [...], "source_row_count": 500, "metadata": {...}, "query": {...}}`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:675-686` — `summary = {"type": "scalar", "value": result, "rows_scanned": source_row_count or rows}` returned with `"table": None, "source_rows": source_rows, "source_row_count": source_row_count, "metadata": metadata, "query": query`

### Claim 16
- **Doc**: lines 75-83: dict result structure `{"summary": {"type": "dict", "values": {...}, "rows_scanned": 500}, "table": None, "source_rows": [...], "source_row_count": 500, "metadata": {...}, "query": {...}}`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:656-668` — `summary = {"type": "dict", "values": result, "rows_scanned": source_row_count or rows}` returned with `"table": None, "source_rows": source_rows, "source_row_count": source_row_count, "metadata": metadata, "query": query`

### Claim 17
- **Doc**: line 87: "`assistant/tools/__init__.py` → `run_query()` → bridges interpreter and chat"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:123` — `def run_query(query: dict, df, sessions: dict) -> dict:`

### Claim 18
- **Doc**: lines 89-97: `run_query()` returns `{"model_response": ..., "table": [...], "source_rows": [...], "source_row_count": 80, "chart": {...}}`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:136-142` — returns exactly these five keys: `model_response`, `table`, `source_rows`, `source_row_count`, `chart`

### Claim 19
- **Doc**: line 101: function name `_format_summary_for_model()`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:151` — `def _format_summary_for_model(summary: dict) -> str:`

### Claim 20
- **Doc**: line 105: scalar format `Result: 80 (from 500 rows)`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:159` — `return f"Result: {value} (from {rows_scanned} rows)"`

### Claim 21
- **Doc**: line 106: dict format `Result: count=80, mean=67.3, max=156.2`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:164-165` — `parts = [f"{k}={v}" for k, v in values.items()]` then `return f"Result: {', '.join(parts)}"`

### Claim 22
- **Doc**: line 107: table format starts with `Result: 13 rows\n  change_pct: min=..., max=...`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:168` — `lines = [f"Result: {summary.get('rows', 0)} rows"]`; line 175 — `lines.append(f"  {col}: min={st['min']}, max={st['max']}{mean_str}")`

### Claim 23
- **Doc**: line 107: table format mean shown as `mean=-3.27`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:174` — `mean_str = f", mean={st['mean']:.2f}"` — mean is formatted to 2 decimal places and appended after max

### Claim 24
- **Doc**: line 108: grouped format `Result: 5 groups by dow\n  min: dow=Fri, mean_gap=32.1\n  max: dow=Mon, mean_gap=89.5`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:188` — `lines = [f"Result: {summary.get('rows', 0)} groups by {summary.get('by', '?')}"]`; lines 192-195 — min/max rows appended

### Claim 25
- **Doc**: lines 112-117: result type table (`select` | `group_by` → type)
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:149-156` — branching: group_by present → grouped DataFrame; select_raw present → scalar or dict; neither → table DataFrame

### Claim 26
- **Doc**: line 121: "Заполняется когда `select` присутствует в запросе (`has_aggregation = True`)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:611` — `has_aggregation = query.get("select") is not None`

### Claim 27
- **Doc**: line 125: "scalar | ДА | Показывает строки которые агрегировались"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:611,614` — scalar result comes from `select_raw` being set, so `has_aggregation=True` and source_rows are populated

### Claim 28
- **Doc**: line 126: "dict | ДА | Показывает строки которые агрегировались"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:611,614` — dict result also comes from `select_raw` being a list, so `has_aggregation=True` and source_rows are populated

### Claim 29
- **Doc**: line 127: "grouped (с explicit select) | ДА | Показывает строки до группировки"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:611` — `has_aggregation = query.get("select") is not None`; when user provides explicit select, source_rows are populated

### Claim 30
- **Doc**: line 128: "grouped (без select, auto count) | НЕТ | has_aggregation = False"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:150` — `select = _normalize_select(select_raw or "count()")` uses auto count, but `barb/interpreter.py:611` — `has_aggregation = query.get("select") is not None` → False when user did not provide select

### Claim 31
- **Doc**: line 129: "table (без select) | НЕТ | table = source, дублирование не нужно"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:611` — `has_aggregation = query.get("select") is not None` → False for table results; source_rows stay None at line 609

### Claim 32
- **Doc**: lines 136-139: stats computed from `map` keys + sort column
  ```python
  summary_columns = set(query.get("map", {}).keys())
  if query.get("sort"):
      sort_col = query["sort"].split()[0]
      summary_columns.add(sort_col)
  ```
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:602-606` — `map_columns = list(query.get("map", {}).keys())`, `sort_col = query.get("sort", "").split()[0] if query.get("sort") else None`, `summary_columns = set(map_columns)`, `if sort_col: summary_columns.add(sort_col)`

### Claim 33
- **Doc**: line 142: "Stats включает `min`, `max`, `mean` для каждой числовой колонки"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:713-717` — `stats[col] = {"min": float(df[col].min()) ..., "max": float(df[col].max()) ..., "mean": float(df[col].mean()) ...}`

### Claim 34
- **Doc**: line 146: "first/last: первая и последняя строка с колонками `['date', 'time'] + map_columns`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:723` — `first_last_cols = ["date", "time"] + map_columns`

### Claim 35
- **Doc**: line 146: "Только колонки которые реально существуют в serialized output"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:725` — `first_last_cols = [c for c in first_last_cols if c in table[0]]`

### Claim 36
- **Doc**: line 146: "`last` не включается если всего 1 строка"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:732` — `if last_row and len(table) > 1: summary["last"] = last_row`

### Claim 37
- **Doc**: line 150: "Только для grouped результатов: `{'category': group_by_column, 'value': first_aggregate_column}`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:636-643` — `if is_grouped:` then `chart = {"category": category, "value": value_cols[0]}`

### Claim 38
- **Doc**: line 150: "UI использует для рендера bar chart"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:297-303` — `if chart: blocks.append({"type": "bar-chart", "category_key": chart["category"], "value_key": chart["value"], "rows": ui_data})`

### Claim 39
- **Doc**: line 154: "`assistant/tools/backtest.py` → `run_backtest_tool()` + `_build_backtest_card()`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:123` — `def run_backtest_tool(...)`; `assistant/tools/backtest.py:160` — `def _build_backtest_card(result: BacktestResult, title: str) -> dict:`

### Claim 40
- **Doc**: lines 160-166: 5-line model summary format for backtest with specific fields
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:292-341` — `_format_summary` generates exactly 5 lines: line1 (headline), line2 (trade stats), line3 (yearly), line4 (exits), line5 (top 3 concentration), joined by `\n`

### Claim 41
- **Doc**: line 168: "0 сделок: `Backtest: 0 trades — entry condition never triggered in this period.`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:286` — `return "Backtest: 0 trades — entry condition never triggered in this period."`

### Claim 42
- **Doc**: line 172: "Тот же формат что и query блоки — `{title, blocks: Block[]}`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:275-278` — `return {"title": card_title, "blocks": [metrics_block, area_block, hbar_block, table_block]}`; `assistant/chat.py:313-314` — query card also returns `{"title": title, "blocks": blocks}`

### Claim 43
- **Doc**: line 175: `"title": "RSI < 30 Long · 71 trades"` format
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:274` — `card_title = f"{title} · {m.total_trades} trades"`

### Claim 44
- **Doc**: line 176: `"type": "metrics-grid"` block with items
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:183-196` — `metrics_block = {"type": "metrics-grid", "items": items}` where items includes Trades, Win Rate, PF, Total P&L, Avg Win, Avg Loss, Max DD, Recovery

### Claim 45
- **Doc**: line 177: metrics-grid items include `{"label": "Trades", "value": "71"}` etc.
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:183-192` — items list starts with `{"label": "Trades", "value": str(m.total_trades)}`, `{"label": "Win Rate", "value": f"{m.win_rate:.1f}%"}`, etc.

### Claim 46
- **Doc**: line 178: area-chart block with `x_key: "date"`, `series`, `data` containing `{date, equity, drawdown}`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:213-221` — `area_block = {"type": "area-chart", "x_key": "date", "series": [...], "data": chart_data}` where `chart_data` items are `{"date": str(t.exit_date), "equity": ..., "drawdown": ...}`

### Claim 47
- **Doc**: line 179: `"type": "horizontal-bar"` block with items having `label`, `value`, `detail`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:233-240` — `exit_items` built with `{"label": ..., "value": round(d["pnl"], 1), "detail": f"{d['count']} trades (W:{d['wins']} L:{d['losses']})"}`

### Claim 48
- **Doc**: line 180: table block with columns `["entry_date", "exit_date", "direction", ...]`
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:261-270` — table columns are `["entry_date", "exit_date", "direction", "entry_price", "exit_price", "pnl", "exit_reason", "bars_held"]`

### Claim 49
- **Doc**: line 186: "Frontend проверяет `isDataBlockEvent()` — наличие `title` + `blocks`"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/lib/api.ts:191-193` — `function isDataBlockEvent(obj: unknown): obj is SSEDataBlockEvent { return has(obj, "title") && has(obj, "blocks"); }`

### Claim 50
- **Doc**: line 188: "Даты в trades — ISO строки (`str(datetime.date)`). Сериализация в `_build_backtest_card()`, не в engine."
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/backtest.py:247-248` — `"entry_date": str(t.entry_date), "exit_date": str(t.exit_date)` — serialization in `_build_backtest_card`, and equity chart line 205 `"date": str(t.exit_date)`

### Claim 51
- **Doc**: line 206: "0 trades" example shows `data_block с пустыми trades и нулевыми metrics`
- **Verdict**: WRONG
- **Evidence**: `assistant/tools/backtest.py:167-176` — 0-trade card returns only a single `metrics-grid` block with one item `{"label": "Trades", "value": "0"}`. No trades table, no equity chart, no separate empty-trades component.
- **Fix**: Change description to: "data_block с одним metrics-grid: только `Trades: 0`"

### Claim 52
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/tools/backtest.py:178-180` — `pf = f"{m.profit_factor:.2f}" if m.profit_factor != float("inf") else "inf"` and `rf = f"{m.recovery_factor:.2f}" if m.recovery_factor != float("inf") else "inf"` — both metrics-grid PF/Recovery and summary line1/line2 render `inf` as the literal string "inf" when the value is infinity (e.g., all wins). Not documented.
- **Fix**: Add to section "Backtest Result": "PF and Recovery show `inf` (string) when profit factor or recovery factor is infinite (all trades won / no drawdown)"

### Claim 53
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/tools/backtest.py:180,194` — `pnl_color = "green" if m.total_pnl > 0 else "red" if m.total_pnl < 0 else None`; `if pnl_color: items[3]["color"] = pnl_color` — Total P&L item in metrics-grid gets an optional `"color"` field. Not documented anywhere in result-format.md.
- **Fix**: Add to section "Backtest Result / Формат для UI": metrics-grid items may have optional `"color"` field (`"green"` or `"red"`) applied to Total P&L

### Claim 54
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/chat.py:278-314` — `_build_query_card()` function in chat.py assembles the actual `{title, blocks}` for query results, adding a `bar-chart` block for grouped results before the `table` block. result-format.md describes the interpreter and tool layers but does not describe the query card assembly layer.
- **Fix**: Add section between "Tool layer" and "Backtest Result" describing `_build_query_card()` in `assistant/chat.py` and the typed block format it produces: `{type: "bar-chart", category_key, value_key, rows}` + `{type: "table", columns, rows}`

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 50 |
| OUTDATED | 0 |
| WRONG | 1 |
| MISSING | 3 |
| UNVERIFIABLE | 0 |
| **Total** | **54** |
| **Accuracy** | **93%** |

Accuracy = 50 / 54 × 100 = 92.6%
