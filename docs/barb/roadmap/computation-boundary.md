# Computation Boundary

## Principle

**The model translates and presents. The engine computes.**

If the model does arithmetic, plans multi-step computation, or manages data flow — the engine is missing a capability.

## The Chain

```
User question
  → Model (translator): question → query JSON
    → Engine: query → result
      → Tool layer: result → summary (model) + table (UI)
        → Model (responder): summary → text
          → User sees: text + table/chart
```

| Component | Job |
|---|---|
| Model (translator) | Convert question to query JSON |
| Engine | Execute computation |
| Tool layer | Format: summary for model, table for UI |
| Model (responder) | Present result in human language |
| Frontend | Render table and chart |

The model doesn't see raw data — by design. The summary is lossy (row count, stats, first/last row). This forces high-level statements and prevents the model from regurgitating data. The user sees the full table in the UI.

## Where Boundaries Are Wrong

### 1. Model does arithmetic

User: "What percentage of days had gap up in 2024?"

```
Now:    Model runs TWO queries (count all + count filtered), divides in its head.
Should: Model writes ONE query: select pct(gap_pct() > 0). Engine returns 0.583.
```

The engine has no `pct()` function. The model compensates with arithmetic.

### 2. Model manages data flow

User: "Find oversold days, then show what happened next."

```
Now:    Model runs query 1, sees summary, tries to reference those rows in query 2.
        Can't — queries are independent. Reconstructs condition or makes up dates.
Should: Model writes ONE query with two steps. Engine chains them internally.
```

The engine can only run one flat pipeline per query. The model compensates by managing data flow across multiple tool calls.

### 3. Engine computes on wrong data

User: "Between 6am and 4pm, at which hour does the session high form?"

```
Now:    Model writes map: {sh: session_high()}, where: hour() >= 6.
        Engine runs map BEFORE where. session_high() sees all bars, not just 6am-4pm.
        Result is wrong. Model and user don't know.
Should: Model writes two steps: step 1 filters to window, step 2 computes on filtered data.
```

The engine's fixed pipeline order (map before where) prevents correct computation. Multi-step queries solve this because each step runs the full pipeline.

## Two Changes

### 1. `pct(condition)` — percentage aggregate

```
select: "pct(gap_pct() > 0)"
```

Engine evaluates condition → boolean Series → `sum() / len()`. Returns scalar.

Same pattern as existing aggregates. Fits both execution paths:
- Non-grouped: `pct(df, bool_series)` → scalar (via `evaluate()`)
- Grouped: `pct(col)` = `mean` of boolean column (via `groups[col].agg("mean")`)

One query, one result. Model translates, engine computes.

### 2. `steps` — multi-step queries

```json
{"steps": [
  {"from": "daily", "map": {"rsi": "rsi(close,14)"}, "where": "rsi < 30"},
  {"map": {"ret": "change_pct(close, 5)"}, "select": "mean(ret)"}
], "title": "Return after oversold"}
```

One tool call. Model describes the full task. Engine chains steps:

```python
def execute(query, df, sessions):
    if "steps" in query:
        steps = query["steps"]
        for i, step in enumerate(steps):
            if i == 0:
                df = _run_pipeline(step, df, sessions)  # session → period → from → map → where
            else:
                df = _run_pipeline_inner(step, df)       # map → where
        last = steps[-1]
        return _finalize(df, last)                       # group_by → select → sort → limit
    # ... existing flat pipeline unchanged
```

No state. No saving. No naming. `df` is a local variable overwritten in a loop. Like `cat | grep | sort` — output of one step is input to the next.

**Step 1** runs the full pipeline: session → period → from → map → where. This scopes the data.

**Steps 2+** inherit the DataFrame from the previous step. Only run map → where (compute and filter on the existing data). `session`, `period`, `from` are ignored — data is already scoped.

**Last step** runs group_by → select → sort → limit to produce the final result. Only the final result goes to the tool layer. Model sees one summary.

**Without `steps`**: query works exactly as before. Flat pipeline, single step. No breaking changes.

### What steps solves

**Follow-up analysis:**
```json
{"steps": [
  {"from": "daily", "map": {"rsi": "rsi(close,14)"}, "where": "rsi < 30"},
  {"map": {"ret": "change_pct(close, 5)"}, "select": "mean(ret)"}
]}
```
Step 1 finds oversold days. Step 2 computes average 5-day return on those rows.

**Sub-window computation:**
```json
{"steps": [
  {"session": "ETH", "period": "last_50", "from": "1m", "where": "hour() >= 6 and hour() <= 16"},
  {"map": {"sh": "session_high()"}, "where": "high == sh", "group_by": "hour()", "select": "count()"}
]}
```
Step 1 filters to 6am-4pm window. Step 2 computes session_high() on the window only.

**Breakdown of filtered data:**
```json
{"steps": [
  {"from": "daily", "map": {"rsi": "rsi(close,14)"}, "where": "rsi < 30"},
  {"map": {"mo": "monthname()"}, "group_by": "mo", "select": "count()"}
]}
```
Step 1 finds signal days. Step 2 groups by month. Model gets the breakdown from the engine.

**Percentages:** No steps needed. `pct()` handles it in one flat query.

## What This Doesn't Cover

**Cross-timeframe** — step 1 produces daily rows, step 2 needs minute data for those dates. Requires loading different raw data mid-pipeline. Separate problem.

**Cross-instrument** — comparing two instruments requires two DataFrames. Outside current architecture.

## Implementation

```
barb/functions/aggregate.py  — add pct (AGGREGATE_FUNCTIONS + AGGREGATE_FUNCS + SIGNATURES + DESCRIPTIONS)
barb/interpreter.py          — add steps to _VALID_FIELDS, loop in execute(), extract _run_pipeline / _run_pipeline_inner
assistant/tools/__init__.py  — add steps to schema + description, add pct pattern, remove "TWO queries" instruction
tests/                       — pct (scalar, grouped, empty), steps (chain, sub-window, breakdown, flat unchanged)
```

~40 lines interpreter + ~15 lines aggregate + tool description + tests.
