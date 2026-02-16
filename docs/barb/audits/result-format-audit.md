# Audit: result-format.md

**Date**: 2026-02-16
**Claims checked**: 42
**Correct**: 39 | **Wrong**: 1 | **Outdated**: 0 | **Unverifiable**: 2

## Issues

### [WRONG] Data flow diagram omits several SSE event types
- **Doc says**: SSE events are `text_delta`, `data_block`, and `done`
- **Code says**: Chat stream also yields `tool_start`, `tool_end` events; API layer adds `title_update`, `persist`, and `error` SSE events
- **File**: `/Users/yura/Development/barb/assistant/chat.py`:133-183 (tool_start/tool_end), `/Users/yura/Development/barb/api/main.py`:686,701,724 (title_update/error/persist)

### [UNVERIFIABLE] Example data values
- **Doc says**: Various example values like `rows: 13`, `change_pct: min=-5.06`, `mean_gap=32.1`, etc.
- **Reason**: These are illustrative examples, not verifiable against code logic. The structure is correct, values are plausible.

### [UNVERIFIABLE] Russian-language descriptions of user intent
- **Doc says**: e.g., "сколько inside days?", "средний gap по dow", etc.
- **Reason**: These are usage examples showing typical questions, not verifiable against code.

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Interpreter response is built in `barb/interpreter.py` -> `execute()` -> `_build_response()` | CORRECT | `interpreter.py`:90,588 |
| 2 | DataFrame result summary has `type: "table"` or `"grouped"` | CORRECT | `interpreter.py`:696 — `"type": "grouped" if is_grouped else "table"` |
| 3 | Summary includes `rows` field with row count | CORRECT | `interpreter.py`:697 — `"rows": len(table)` |
| 4 | Summary includes `columns` field from DataFrame columns | CORRECT | `interpreter.py`:698 — `"columns": list(df.columns)` |
| 5 | Summary includes `stats` with `min`, `max`, `mean` per numeric column | CORRECT | `interpreter.py`:706-715 |
| 6 | Summary includes `first` and `last` row data | CORRECT | `interpreter.py`:718-729 |
| 7 | Grouped summary adds `by` field | CORRECT | `interpreter.py`:703 — `summary["by"] = group_by if isinstance(group_by, str) else group_by[0]` |
| 8 | Grouped summary adds `min_row` and `max_row` | CORRECT | `interpreter.py`:732-740 |
| 9 | `table` field contains full serialized data for UI | CORRECT | `interpreter.py`:618 — `table = _serialize_records(prepared.to_dict("records"))` |
| 10 | `source_rows` contains rows before aggregation | CORRECT | `interpreter.py`:605-613 |
| 11 | `source_row_count` counts rows that participated | CORRECT | `interpreter.py`:611 — `source_row_count = len(source_df)` |
| 12 | `chart` is `{"category": ..., "value": ...}` only for grouped | CORRECT | `interpreter.py`:631-639 |
| 13 | `chart` is `None` for non-grouped table results | CORRECT | `interpreter.py`:631 — `chart = None` stays None when not grouped |
| 14 | `chart` key is absent for scalar/dict results | CORRECT | `interpreter.py`:658-665 (dict), 676-683 (scalar) — no `chart` key |
| 15 | `metadata` includes `rows`, `session`, `from`, `warnings` | CORRECT | `interpreter.py`:590-595 |
| 16 | Scalar result has `summary.type = "scalar"`, `value`, `rows_scanned` | CORRECT | `interpreter.py`:671-675 |
| 17 | Scalar result has `table: None` | CORRECT | `interpreter.py`:678 |
| 18 | Dict result has `summary.type = "dict"`, `values`, `rows_scanned` | CORRECT | `interpreter.py`:653-657 |
| 19 | Dict result has `table: None` | CORRECT | `interpreter.py`:660 |
| 20 | `run_query()` is in `assistant/tools/__init__.py` | CORRECT | `assistant/tools/__init__.py`:61 |
| 21 | `run_query()` returns `model_response`, `table`, `source_rows`, `source_row_count`, `chart` | CORRECT | `assistant/tools/__init__.py`:74-80 |
| 22 | `_format_summary_for_model()` exists and formats summary to string | CORRECT | `assistant/tools/__init__.py`:89 |
| 23 | Scalar format: `Result: {value} (from {rows_scanned} rows)` | CORRECT | `assistant/tools/__init__.py`:97 |
| 24 | Dict format: `Result: count=80, mean=67.3, max=156.2` | CORRECT | `assistant/tools/__init__.py`:101-103 |
| 25 | Table format: `Result: N rows` + stats + first/last | CORRECT | `assistant/tools/__init__.py`:106-123 |
| 26 | Grouped format: `Result: N groups by {col}` + min/max | CORRECT | `assistant/tools/__init__.py`:125-136 |
| 27 | No select + no group_by = table type | CORRECT | `interpreter.py`:153-154 — `result_df = df` |
| 28 | scalar select + no group_by = scalar type | CORRECT | `interpreter.py`:150-152 — `_aggregate` returns scalar for string select |
| 29 | list select + no group_by = dict type | CORRECT | `interpreter.py`:150-152 — `_aggregate` returns dict for list select |
| 30 | Any select + group_by = grouped type | CORRECT | `interpreter.py`:147-149 — `_group_aggregate` returns DataFrame |
| 31 | `source_rows` populated when `select` is present (`has_aggregation = True`) | CORRECT | `interpreter.py`:607-613 |
| 32 | Grouped without explicit select (auto count) has no source_rows | CORRECT | `interpreter.py`:607 — `query.get("select") is not None` is False |
| 33 | Table without select has no source_rows | CORRECT | `interpreter.py`:607 — `query.get("select") is not None` is False |
| 34 | Stats columns = map keys + sort column | CORRECT | `interpreter.py`:598-602 |
| 35 | First/last rows use `["date", "time"] + map_columns` | CORRECT | `interpreter.py`:719 |
| 36 | `last` excluded when only 1 row | CORRECT | `interpreter.py`:728 — `if last_row and len(table) > 1` |
| 37 | Chart hint: `{"category": group_by_column, "value": first_aggregate_column}` | CORRECT | `interpreter.py`:634-639 |
| 38 | SSE data_block contains `{tool, input, result, rows, title, chart}` | CORRECT | `chat.py`:199-206 |
| 39 | SSE done contains `{answer, usage, tool_calls, data}` | CORRECT | `chat.py`:253-261 |
| 40 | SSE text_delta contains `{delta: text}` | CORRECT | `chat.py`:91 |
| 41 | Data flow diagram shows only text_delta, data_block, done SSE events | WRONG | `chat.py`:133,176 also yield `tool_start`, `tool_end`; `api/main.py`:686,701,724 add `title_update`, `error`, `persist` |
| 42 | `query` field included in interpreter response | CORRECT | `interpreter.py`:648,664,682 |
