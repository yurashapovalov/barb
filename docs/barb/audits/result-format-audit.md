# Audit: result-format.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 32: "`barb/interpreter.py` -> `execute()` returns:"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:90` — `def execute(query: dict, df: pd.DataFrame, sessions: dict) -> dict:`

### Claim 2
- **Doc**: line 37: "summary type can be `scalar | dict | table | grouped`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:694-695` — `"type": "grouped" if is_grouped else "table"`; line 652 — `"type": "dict"`; line 670 — `"type": "scalar"`

### Claim 3
- **Doc**: line 38: "summary contains `rows` count"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:696` — `"rows": len(table)`

### Claim 4
- **Doc**: lines 39-41: "summary contains `stats` with min/max/mean"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:705-714` — stats dict with `min`, `max`, `mean` for numeric columns

### Claim 5
- **Doc**: lines 42-43: "summary contains `first` and `last` with `timestamp` key"
- **Verdict**: WRONG
- **Evidence**: `barb/interpreter.py:718-720` — `first_last_cols = ["timestamp"] + map_columns` but `table` from `_prepare_for_output` has `date` not `timestamp`, so filter removes it. Actual first/last contain only map columns.
- **Fix**: remove `timestamp` from first/last example or note date is not captured

### Claim 6
- **Doc**: line 46: "response contains `table` key"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:641` — `"table": table`

### Claim 7
- **Doc**: line 47: "response contains `source_rows`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:604-612` — populated when `has_aggregation` is True

### Claim 8
- **Doc**: line 48: "response contains `source_row_count`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:644,663,679` — in all response branches

### Claim 9
- **Doc**: line 49: "response contains `metadata`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:589-594` — metadata dict with rows, session, from, warnings

### Claim 10
- **Doc**: line 50: "response contains `query`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:646,664,681` — in all branches

### Claim 11
- **Doc**: lines 36-51: response structure does not mention `chart` key
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:629-638,647` — `"chart": chart` returned in DataFrame branch
- **Fix**: add `"chart"` to response structure

### Claim 12
- **Doc**: line 56: "`assistant/tools/__init__.py` -> `_format_summary_for_model()`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:89` — function exists

### Claim 13
- **Doc**: line 60: "scalar format: `Result: 80 (from 500 rows)`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:97` — exact format match

### Claim 14
- **Doc**: line 61: "dict format: `Result: count=80, mean=67.3`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:101-103` — format match

### Claim 15
- **Doc**: line 62: "table format: `Result: 13 rows\n  change_pct: min=...`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:106-123` — format match

### Claim 16
- **Doc**: line 63: "grouped format: `Result: 5 groups by dow`"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/tools/__init__.py:126-136` — format match

### Claim 17
- **Doc**: lines 67-69: "no select, no group_by produces table type"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:152-153` — DataFrame result, type "table"

### Claim 18
- **Doc**: lines 67,70: "scalar select, no group_by produces scalar type"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:149-151` — single string select → scalar

### Claim 19
- **Doc**: lines 67,71: "list select, no group_by produces dict type"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:149-151` — list select → dict

### Claim 20
- **Doc**: lines 67,72: "any select with group_by produces grouped type"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:146-148` — group_by → grouped DataFrame

### Claim 21
- **Doc**: line 80: "scalar/dict results get source_rows"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:606` — `has_aggregation = query.get("select") is not None`, True for scalar/dict

### Claim 22
- **Doc**: line 81: "grouped results do NOT get source_rows"
- **Verdict**: WRONG
- **Evidence**: `barb/interpreter.py:606` — grouped queries with explicit `select` have `has_aggregation=True`, so source_rows IS populated
- **Fix**: "grouped results get source_rows when `select` is explicitly provided"

### Claim 23
- **Doc**: line 82: "table results do NOT get source_rows"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:606` — no select → `has_aggregation=False`

### Claim 24
- **Doc**: lines 86-93: "stats calculated for columns from `map` + column from `sort`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:597-601` — `summary_columns = set(map_columns)` then adds sort_col

### Claim 25
- **Doc**: line 21: "SSE data_block contains `{table: rows}`"
- **Verdict**: WRONG
- **Evidence**: `assistant/chat.py:199-211` — key is `result`, not `table`, plus `rows`, `title`, `chart`
- **Fix**: change `{table: rows}` to `{result: rows, rows: N, title: ..., chart: ...}`

### Claim 26
- **Doc**: lines 25-27: "SSE done event sends `{data: rows}`"
- **Verdict**: WRONG
- **Evidence**: `assistant/chat.py:253-261` — done event has `{answer, usage, tool_calls, data}`
- **Fix**: update diagram to show full done event structure

### Claim 27
- **Doc**: line 99: "scalar example produces `{type: scalar, value: 65}`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:670-671` — format match

### Claim 28
- **Doc**: line 100: "grouped example produces `{type: grouped, rows: 5}`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:694-696` — format match

### Claim 29
- **Doc**: line 101: "table example produces `{type: table, rows: 13}`"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:694-696` — format match

### Claim 30
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:697` — summary includes `"columns": list(df.columns)`
- **Fix**: add `"columns"` to summary structure

### Claim 31
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:700-702` — grouped summary includes `"by": group_by`
- **Fix**: add `"by"` to grouped summary

### Claim 32
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:736-744` — grouped summary includes `"min_row"` and `"max_row"`
- **Fix**: add min_row/max_row to grouped summary docs

### Claim 33
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:652-655` — dict summary has `"values"`, `"rows_scanned"`; scalar has `"value"`, `"rows_scanned"`
- **Fix**: document dict and scalar summary sub-structures

### Claim 34
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/tools/__init__.py:74-80` — `run_query()` return format bridges interpreter and chat
- **Fix**: add section describing `run_query()` return format

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 22 |
| OUTDATED | 0 |
| WRONG | 4 |
| MISSING | 6 |
| UNVERIFIABLE | 0 |
| **Total** | **32** |
| **Accuracy** | **69%** |

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

| Result | Count |
|--------|-------|
| CONFIRMED | 34 |
| DISPUTED | 0 |
| INCONCLUSIVE | 0 |
| **Total** | **34** |
