# Barb Script — Language Specification

## 1. Overview

Barb Script is a declarative query language for OHLCV time series analysis. It exists to solve one problem: LLMs generate buggy pandas code. Instead, the LLM generates a structured JSON query, and a deterministic interpreter executes it.

```
User question → LLM → JSON query → Interpreter → Result
```

The LLM can make logical mistakes (wrong column, wrong filter), but it **cannot** produce runtime errors, syntax bugs, or security issues. The interpreter handles all execution.

A query is a flat JSON object. The interpreter decides execution order. The LLM only declares **what** to compute, not **how**.

---

## 2. Data Model

### 2.1 Source

All data originates as 1-minute OHLCV bars:

| Column    | Type     | Description              |
|-----------|----------|--------------------------|
| timestamp | datetime | Bar timestamp (index)    |
| open      | float    | Opening price            |
| high      | float    | Highest price            |
| low       | float    | Lowest price             |
| close     | float    | Closing price            |
| volume    | int      | Number of contracts      |

Timezone: ET (Eastern Time). This is the data timezone, not the exchange native timezone.

### 2.2 Timeframes

Source data is 1-minute bars. They can be resampled to any of these fixed timeframes:

**Minutes:**

| Timeframe | Description          | Resample rule |
|-----------|----------------------|---------------|
| `1m`      | Original data        | (none)        |
| `5m`      | 5-minute bars        | `5min`        |
| `15m`     | 15-minute bars       | `15min`       |
| `30m`     | 30-minute bars       | `30min`       |

**Hours:**

| Timeframe | Description          | Resample rule |
|-----------|----------------------|---------------|
| `1h`      | 1-hour bars          | `h`           |
| `2h`      | 2-hour bars          | `2h`          |
| `4h`      | 4-hour bars          | `4h`          |

**Days and above:**

| Timeframe   | Description          | Resample rule |
|-------------|----------------------|---------------|
| `daily`     | 1-day bars           | `D`           |
| `weekly`    | 1-week bars          | `W`           |
| `monthly`   | 1-month bars         | `ME`          |
| `quarterly` | 1-quarter bars       | `QE`          |
| `yearly`    | 1-year bars          | `YE`          |

This is a fixed list. No arbitrary intervals — these are the standard timeframes used on all trading platforms (TradingView, NinjaTrader, Sierra Chart).

**Session requirement:** For `daily` and above, session defines what bars are built from. "Daily RTH bar" and "daily ETH bar" are different — different open, different high/low, different range. Session must be specified for these timeframes. For intraday timeframes (`1m`–`4h`), session is optional (filters which hours are included).

Resample aggregation (fixed, not configurable):
- open → first
- high → max
- low → min
- close → last
- volume → sum

Rows where all OHLCV values are NaN are dropped after resample.

### 2.3 Sessions

Sessions define time-of-day filters. They are **instrument-specific** and loaded from configuration at runtime. They are NOT hardcoded in the language.

Example configuration for NQ:

```
RTH:        09:30 — 17:00
ETH:        18:00 — 17:00  (wraps midnight)
OVERNIGHT:  18:00 — 09:30  (wraps midnight)
ASIAN:      18:00 — 03:00  (wraps midnight)
EUROPEAN:   03:00 — 09:30
MORNING:    09:30 — 12:30
AFTERNOON:  12:30 — 17:00
RTH_OPEN:   09:30 — 10:30
RTH_CLOSE:  16:00 — 17:00
```

Wrap-around sessions (start > end) span midnight. The filter includes bars where `time >= start OR time < end`.

A different instrument (e.g., CL, ES) may have completely different sessions.

### 2.4 Value Types

| Type     | Examples                  | Usage                          |
|----------|---------------------------|--------------------------------|
| float    | `3.14`, `-0.5`            | Prices, computed values        |
| int      | `42`, `0`                 | Volume, counts, weekday        |
| bool     | `true`, `false`           | Filter conditions              |
| string   | `"FOMC"`, `"up"`          | Event types, categories        |
| datetime | (index only)              | Timestamp                      |
| NaN      | (missing value)           | Result of prev() on first row  |

### 2.5 External Sources

Available for JOIN operations:

**events** — market events with known dates:

| Column         | Type   | Description                         |
|----------------|--------|-------------------------------------|
| date           | date   | Event date                          |
| event_id       | string | Identifier: `fomc`, `nfp`, `opex`   |
| event_name     | string | Human name: `"FOMC Rate Decision"`  |
| event_category | string | `macro`, `options`                   |
| event_impact   | string | `high`, `medium`, `low`              |
| event_time     | string | Time of release: `"14:00"` or null  |

**holidays** — market closures and early closes:

| Column     | Type   | Description                          |
|------------|--------|--------------------------------------|
| date       | date   | Holiday date                         |
| name       | string | `"Christmas"`, `"Thanksgiving"`      |
| day_type   | string | `closed`, `early_close`              |
| close_time | string | `"13:15"` for early close, null      |

Which events and holidays are available depends on instrument configuration.

---

## 3. Query Format

A query is a flat JSON object with optional fields:

```json
{
  "session":  "RTH",
  "from":     "daily",
  "join":     {"source": "events", "filter": "event_id == 'fomc'"},
  "map":      {"range": "high - low", "gap": "open - prev(close)"},
  "where":    "gap > 0 and close > open",
  "group_by": "weekday",
  "select":   "mean(range)",
  "sort":     "mean_range desc",
  "limit":    10
}
```

### 3.1 Field Reference

| Field      | Type                | Default     | Description                        |
|------------|---------------------|-------------|------------------------------------|
| `session`  | string \| null      | null        | Session name from instrument config. Required for `daily`+ timeframes. |
| `from`     | string              | `"1m"`      | Timeframe: `1m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `daily`, `weekly`, `monthly`, `quarterly`, `yearly` (see 2.2) |
| `period`   | string \| null      | null        | Date range filter: `"2024"`, `"2024-01"`, `"2024-01-01:2024-12-31"`, `"last_year"`, `"last_month"`, `"last_week"`. null = all data. |
| `join`     | object \| null      | null        | External data source to join       |
| `map`      | object \| null      | null        | Computed columns: `{name: expr}`   |
| `where`    | string \| null      | null        | Row filter expression (boolean)    |
| `group_by` | string \| list \| null | null     | Column(s) to group by              |
| `select`   | string \| list      | `"count()"` | Aggregate expression(s)            |
| `sort`     | string \| null      | null        | Sort: `"column [asc|desc]"`        |
| `limit`    | int \| null         | null        | Max rows to return                 |

### 3.2 Field Details

**session** — Filters minute-level data by time of day before any other operation. Value must match a session name from the instrument's configuration. Case-insensitive. Required for `daily` and above timeframes — defines what a "day" means (RTH day vs full trading day).

**period** — Filters data by date range. Formats:
- Year: `"2024"` — all data in 2024
- Month: `"2024-01"` — January 2024
- Range: `"2024-01-01:2024-12-31"` — explicit start:end
- Relative: `"last_year"`, `"last_month"`, `"last_week"` — relative to current date
- null — all available data (default)

**from** — Resamples data to the specified timeframe. One of the fixed list: `"1m"`, `"5m"`, `"15m"`, `"30m"`, `"1h"`, `"2h"`, `"4h"`, `"daily"`, `"weekly"`, `"monthly"`, `"quarterly"`, `"yearly"`. Default is `"1m"` (no resampling). For `daily` and above, `session` must be specified — see 2.2.

**join** — Joins an external data source by date:
```json
{
  "source": "events",
  "filter": "event_id == 'fomc'"
}
```
- `source` (required): Name of external source (`"events"`, `"holidays"`)
- `filter` (optional): Expression to filter the external source before joining

After join, the external source's columns become available in `map`, `where`, and `group_by`.

**map** — Declares computed columns. Keys are new column names, values are expressions:
```json
{
  "range": "high - low",
  "weekday": "dayofweek()",
  "is_inside": "high < prev(high) and low > prev(low)"
}
```
Columns are computed in declaration order. Later columns can reference earlier ones.

**Complexity rule:** Each expression in `map` should be simple — one or two operations. Complex logic must be broken into intermediate columns:

Good — simple steps:
```json
{
  "gap": "open - prev(close)",
  "gap_is_up": "gap > 0",
  "filled_up": "gap_is_up and low <= prev(close)",
  "filled_down": "not gap_is_up and high >= prev(close)",
  "gap_filled": "filled_up or filled_down"
}
```

Bad — everything in one expression:
```json
{
  "gap_filled": "if(open - prev(close) > 0, low <= prev(close), high >= prev(close))"
}
```

Both produce the same result, but the first is easier to validate and debug.

**where** — Boolean expression to filter rows. Only rows where the expression evaluates to `true` are kept. Can reference base columns, map columns, and joined columns.

**group_by** — Column name or list of column names to group by. When present, `select` is applied per group. Result is a table with group columns + aggregate columns.

**select** — What to compute from the (possibly grouped) data:
- Single aggregate: `"mean(range)"` → returns scalar (or Series if grouped)
- Multiple aggregates: `["mean(range)", "count()"]` → returns DataFrame
- Without `group_by`: returns scalar value(s)
- With `group_by`: returns DataFrame with one row per group

**sort** — Format: `"column_name [asc|desc]"`. Default direction is `asc`. The column must exist in the result. For aggregate results, the column name is `{func}_{col}` (e.g., `mean_range`). For `count()`, the column name is `count`.

**limit** — Maximum number of rows in the result. Applied after sort.

### 3.3 Minimal Query

The simplest valid query:
```json
{}
```
Returns all minute-level data as-is.

A common minimal query:
```json
{"from": "daily", "select": "count()"}
```
Returns the number of daily bars.

---

## 4. Execution Order

The interpreter executes query fields in a fixed order, regardless of their position in the JSON:

```
1. SESSION    — filter minute data by time of day
2. PERIOD     — filter by date range
3. FROM       — resample to target timeframe
4. JOIN       — attach external data
5. MAP        — compute derived columns
6. WHERE      — filter rows
7. GROUP BY   — group rows
8. SELECT     — aggregate (per group or overall)
9. SORT       — order result rows
10. LIMIT     — truncate result
```

### Why this order

| Step | Reason |
|------|--------|
| SESSION first | Sessions are time-of-day filters. After resample to daily, time information is lost. Must filter first. |
| PERIOD before FROM | Reduces data volume before resample. No point resampling years we don't need. |
| FROM before JOIN | External sources (events) are date-level. Joining makes sense only after data is at daily+ granularity. |
| JOIN before MAP | Map expressions may reference joined columns (e.g., `event_category`). |
| MAP before WHERE | Filter expressions may reference computed columns (e.g., `where: "range > 10"` requires `map: {"range": "high - low"}`). |
| WHERE before GROUP | Filtering reduces the dataset before grouping. |
| GROUP before SELECT | Aggregation is applied per group. |
| SORT and LIMIT last | Ordering and truncation on the final result. |

### Step behavior

- If a field is `null` or absent, the step is skipped.
- Each step receives the DataFrame from the previous step.
- Steps 1-5 produce a DataFrame.
- Step 6-7 (GROUP+SELECT) produces a DataFrame (grouped) or scalar (ungrouped).
- Steps 8-9 only apply if the result is a DataFrame.

---

## 5. Expression Language

Expressions are strings that describe computations over columns. They appear in `map` values, `where`, `select`, and `join.filter`.

### 5.1 Literals

| Type    | Syntax                    | Examples               |
|---------|---------------------------|------------------------|
| Integer | digits                    | `42`, `0`, `-1`        |
| Float   | digits with dot           | `3.14`, `-0.5`, `1.0`  |
| String  | double quotes             | `"FOMC"`, `"up"`       |
| Boolean | keywords                  | `true`, `false`        |
| List    | brackets (only with `in`) | `[0, 1, 4]`, `["a"]`  |

### 5.2 Column References

Any unquoted identifier that is not a function name or keyword is a column reference.

**Base columns** (always available): `open`, `high`, `low`, `close`, `volume`

**Computed columns** (available after `map`): any name defined in `map`

**Joined columns** (available after `join`): columns from the external source

**Time-derived** (available via time functions in `map`): `dayofweek()`, `hour()`, etc.

Column names must be valid identifiers: start with a letter or underscore, contain only letters, digits, and underscores.

### 5.3 Operators

**Arithmetic** (operate element-wise on Series):

| Operator | Description    | Example            |
|----------|----------------|--------------------|
| `+`      | Addition       | `high + low`       |
| `-`      | Subtraction    | `close - open`     |
| `*`      | Multiplication | `close * volume`   |
| `/`      | Division       | `range / close`    |

Division by zero produces `NaN`.

**Comparison** (produce boolean Series):

| Operator | Description      | Example             |
|----------|------------------|---------------------|
| `>`      | Greater than     | `close > open`      |
| `<`      | Less than        | `volume < 1000`     |
| `>=`     | Greater or equal | `high >= prev(high)`|
| `<=`     | Less or equal    | `low <= prev(low)`  |
| `==`     | Equal            | `weekday == 1`      |
| `!=`     | Not equal        | `gap != 0`          |

**Logical** (combine boolean Series):

| Operator | Description | Example                            |
|----------|-------------|------------------------------------|
| `and`    | Logical AND | `close > open and volume > 10000`  |
| `or`     | Logical OR  | `weekday == 0 or weekday == 4`     |
| `not`    | Logical NOT | `not (high < prev(high))`          |

**Membership**:

| Operator | Description  | Example                 |
|----------|--------------|-------------------------|
| `in`     | Value in set | `weekday in [0, 1, 4]`  |

**Precedence** (highest to lowest):
1. Function calls, parentheses
2. Unary: `not`, `-`
3. Multiplicative: `*`, `/`
4. Additive: `+`, `-`
5. Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
6. Membership: `in`
7. Logical: `and`
8. Logical: `or`

Use parentheses to override: `(close - open) / (high - low)`

### 5.4 Functions

Functions are categorized by what they do. Each category has distinct behavior.

#### Scalar Functions

Operate on each value independently. Input: value(s). Output: value of the same shape.

| Function            | Signature              | Description                      |
|---------------------|------------------------|----------------------------------|
| `abs(x)`            | number → number        | Absolute value                   |
| `log(x)`            | number → number        | Natural logarithm                |
| `sqrt(x)`           | number → number        | Square root                      |
| `sign(x)`           | number → number        | -1, 0, or 1                      |
| `round(x, n)`       | number, int → number   | Round to n decimal places        |
| `if(cond, then, else)` | bool, any, any → any | Conditional value                |

`if()` evaluates element-wise: for each row, returns `then` if `cond` is true, `else` otherwise.

#### Lag Functions

Access values from other rows relative to the current row.

| Function        | Signature            | Description                       |
|-----------------|----------------------|-----------------------------------|
| `prev(col)`     | column → Series      | Previous row's value (shift 1)    |
| `prev(col, n)`  | column, int → Series | Value n rows back (shift n)       |
| `next(col)`     | column → Series      | Next row's value (shift -1)       |
| `next(col, n)`  | column, int → Series | Value n rows forward (shift -n)   |

- `prev()` on the first row(s) produces `NaN`
- `next()` on the last row(s) produces `NaN`
- `n` must be a positive integer literal

#### Window Functions

Rolling window computations. **Always take exactly 2 arguments**: column/condition and window size.

| Function               | Signature              | Description                 |
|------------------------|------------------------|-----------------------------|
| `rolling_mean(col, n)` | column, int → Series   | Rolling average over n bars |
| `rolling_sum(col, n)`  | column, int → Series   | Rolling sum over n bars     |
| `rolling_max(col, n)`  | column, int → Series   | Rolling maximum over n bars |
| `rolling_min(col, n)`  | column, int → Series   | Rolling minimum over n bars |
| `rolling_std(col, n)`  | column, int → Series   | Rolling std dev over n bars |
| `rolling_count(cond, n)` | bool, int → Series   | How many times condition was true in last n bars |
| `ema(col, n)`          | column, int → Series   | Exponential moving average with span n |

- Window size `n` must be a positive integer literal
- The first `n-1` rows produce `NaN` (not enough data for full window)
- Window is trailing (includes current row and n-1 previous rows)
- `ema` uses exponential weighting — more weight on recent bars, standard in trading

#### Cumulative Functions

Expanding window from the start of the dataset. No window size — always from the first row to current.

| Function               | Signature              | Description                 |
|------------------------|------------------------|-----------------------------|
| `cummax(col)`          | column → Series        | Cumulative maximum (all-time high up to this bar) |
| `cummin(col)`          | column → Series        | Cumulative minimum (all-time low up to this bar) |
| `cumsum(col)`          | column → Series        | Cumulative sum from first row to current. Running total. |

#### Pattern Functions

Functions for detecting sequences and relative positioning.

| Function               | Signature              | Description                 |
|------------------------|------------------------|-----------------------------|
| `streak(cond)`         | bool → Series[int]     | Length of current consecutive run where condition is true. Resets to 0 when false. |
| `bars_since(cond)`     | bool → Series[int]     | Number of bars since condition was last true. NaN if never true. |
| `rank(col)`            | column → Series[float] | Percentile rank within the entire column (0.0 to 1.0). 0.95 = value is in the top 5%. |

#### Aggregate Functions

Reduce a column (or the entire DataFrame) to a single value. Used in `select`.

| Function               | Signature                   | Description              |
|------------------------|-----------------------------|--------------------------|
| `mean(col)`            | column → float              | Arithmetic mean          |
| `sum(col)`             | column → float              | Sum of values            |
| `max(col)`             | column → float              | Maximum value            |
| `min(col)`             | column → float              | Minimum value            |
| `std(col)`             | column → float              | Standard deviation       |
| `median(col)`          | column → float              | Median value             |
| `count()`              | → int                       | Number of rows           |
| `percentile(col, p)`   | column, float → float       | p-th percentile (0..1)   |
| `correlation(col1, col2)` | column, column → float   | Pearson correlation      |

- `count()` takes no arguments
- `percentile()` second argument is a float between 0 and 1
- NaN values are excluded from all aggregations

#### Time Functions

Extract components from the row's timestamp (the DataFrame index). Take no arguments — they always operate on the index.

| Function       | Return type | Range   | Description              |
|----------------|-------------|---------|--------------------------|
| `dayofweek()`  | int         | 0-6     | Monday=0, Sunday=6       |
| `hour()`       | int         | 0-23    | Hour of day              |
| `month()`      | int         | 1-12    | Month of year            |
| `year()`       | int         | 2008+   | Year                     |
| `date()`       | date        |         | Date part of timestamp   |
| `day()`        | int         | 1-31    | Day of month             |
| `quarter()`    | int         | 1-4     | Quarter of year          |

#### Session Functions

Access OHLCV values of a specific session within each day. Used in `map` for cross-session analysis.

| Function                  | Signature          | Description                              |
|---------------------------|--------------------|------------------------------------------|
| `session_open(session)`   | string → Series    | First open of the session for each day   |
| `session_high(session)`   | string → Series    | Max high of the session for each day     |
| `session_low(session)`    | string → Series    | Min low of the session for each day      |
| `session_close(session)`  | string → Series    | Last close of the session for each day   |
| `session_volume(session)` | string → Series    | Total volume of the session for each day |

- Argument is a session name string from the instrument config (e.g., `'RTH'`, `'OVERNIGHT'`)
- Only meaningful at `daily` or above timeframe — each row must represent a day
- For each day, the interpreter filters minute data to the session's time range and aggregates
- If the session has no data for a given day, the value is `NaN`
- The `session` query field (top-level filter) and session functions are independent — you can use session functions without setting a `session` filter, or use both together

**Example — correlation between overnight and RTH range:**

```json
{
  "from": "daily",
  "map": {
    "rth_range": "session_high('RTH') - session_low('RTH')",
    "on_range": "session_high('OVERNIGHT') - session_low('OVERNIGHT')"
  },
  "select": "correlation(rth_range, on_range)"
}
```

**Example — real gap (RTH open vs previous RTH close):**

```json
{
  "from": "daily",
  "map": {
    "rth_open": "session_open('RTH')",
    "prev_rth_close": "prev(session_close('RTH'))",
    "gap": "rth_open - prev_rth_close"
  },
  "select": ["mean(gap)", "mean(abs(gap))"]
}
```

**Example — does overnight predict RTH direction?**

```json
{
  "from": "daily",
  "map": {
    "on_direction": "sign(session_close('OVERNIGHT') - session_open('OVERNIGHT'))",
    "rth_direction": "sign(session_close('RTH') - session_open('RTH'))"
  },
  "select": "correlation(on_direction, rth_direction)"
}
```

### 5.5 Expression Contexts

Expressions behave differently depending on where they appear:

| Context        | Expected output  | Example                                    |
|----------------|------------------|--------------------------------------------|
| `map` value    | Series           | `"high - low"` → float Series              |
| `where`        | Boolean Series   | `"close > open"` → bool Series             |
| `select`       | Scalar or Series | `"mean(range)"` → float                    |
| `join.filter`  | Boolean Series   | `"event_id == 'fomc'"` → bool Series       |

**Validation rules:**
- `map` expressions must produce a Series (column-level computation)
- `where` expressions must produce a boolean Series
- `select` expressions must be aggregate function calls
- `join.filter` expressions must produce a boolean Series

---

## 6. Sessions — Detailed Behavior

### 6.1 Configuration

Sessions are defined per instrument as `(start_time, end_time)` pairs in ET:

```python
"sessions": {
    "RTH": ("09:30", "17:00"),
    "OVERNIGHT": ("18:00", "09:30"),
    ...
}
```

### 6.2 Filtering Logic

**Normal session** (start < end, e.g., RTH 09:30—17:00):
Keep rows where `start <= time <= end`.

**Wrap-around session** (start > end, e.g., OVERNIGHT 18:00—09:30):
Keep rows where `time >= start OR time < end`.

### 6.3 Session + Resample Interaction

Session filtering happens on minute-level data **before** resample. This means:

- `session: "RTH", from: "daily"` → daily bars built only from RTH minutes
- `session: null, from: "daily"` → daily bars built from all minutes (full trading day)

This is critical for correct analysis. RTH daily range and ETH daily range are different numbers.

### 6.4 Two Uses of Sessions

Sessions appear in two places with different purposes:

| Mechanism | Purpose | Example |
|-----------|---------|---------|
| `session` field (query-level) | **Filter** — discard all data outside this session | `"session": "RTH"` → only RTH minutes survive |
| `session_*()` functions (in map) | **Access** — read OHLCV of a session per day, keep all data | `session_high('RTH')` → RTH high for each day |

These are independent. Common patterns:

- **Simple analysis** — use `session` field: `{"session": "RTH", "from": "daily", "select": "mean(range)"}`. Most queries.
- **Cross-session** — don't filter, use functions: `{"from": "daily", "map": {"rth_range": "session_high('RTH') - session_low('RTH')", ...}}`.
- **Both** — filter to RTH, but also reference overnight: `{"session": "RTH", "from": "daily", "map": {"on_range": "session_high('OVERNIGHT') - session_low('OVERNIGHT')", ...}}`. The daily bar is RTH, but overnight data is accessed via function.

### 6.5 Unknown Session

If the session name doesn't exist in the instrument config:
- `session` field: skip filtering (use all data) + warning in metadata
- `session_*()` function: return `NaN` for all rows + warning in metadata

---

## 7. JOIN — Detailed Behavior

### 7.1 Join Mechanics

1. The external source is loaded as a DataFrame with a `date` column
2. If `join.filter` is specified, the external source is filtered first
3. A `date` column is derived from the main DataFrame's index (`df.index.date`)
4. Inner join on `date`: only dates present in both sources are kept
5. After join, external source columns are available for `map`, `where`, `group_by`

### 7.2 Example: FOMC days analysis

```json
{
  "from": "daily",
  "join": {"source": "events", "filter": "event_id == 'fomc'"},
  "map": {"range": "high - low"},
  "select": "mean(range)"
}
```

Execution:
1. Resample to daily
2. Load events, filter to FOMC only
3. Inner join → only FOMC days remain
4. Compute range
5. Return mean of range

### 7.3 Multiple Events

To analyze multiple event types:
```json
{
  "from": "daily",
  "join": {"source": "events", "filter": "event_impact == 'high'"},
  "map": {"range": "high - low"},
  "group_by": "event_id",
  "select": "mean(range)"
}
```

### 7.4 No Match

If the join produces zero rows (no matching dates), the result is:
- `count()` → 0
- `mean(col)` → NaN
- DataFrame → empty DataFrame

---

## 8. Type System

### 8.1 Expression Types

Every expression has a type that determines how it can be used:

| Type           | Description                       | Produced by                           |
|----------------|-----------------------------------|---------------------------------------|
| Series[float]  | Column of floats                  | Arithmetic: `high - low`              |
| Series[int]    | Column of ints                    | Time functions: `dayofweek()`         |
| Series[bool]   | Column of booleans                | Comparisons: `close > open`           |
| Series[string] | Column of strings                 | Joined columns: `event_name`          |
| float          | Single float value                | Aggregates: `mean(close)`             |
| int            | Single int value                  | `count()`                             |
| DataFrame      | Table with multiple columns       | GROUP BY result                       |

### 8.2 Type Compatibility

**Arithmetic operators** (`+`, `-`, `*`, `/`):
- Both operands must be numeric (float or int)
- Result is float if either operand is float

**Comparison operators** (`>`, `<`, `>=`, `<=`):
- Both operands must be numeric

**Equality operators** (`==`, `!=`):
- Both operands must be the same type
- Works with float, int, string

**Logical operators** (`and`, `or`, `not`):
- Operands must be boolean

**`in` operator**:
- Left operand: any Series
- Right operand: list of same-type values

### 8.3 NaN Handling

NaN values arise from:
- `prev()` on the first row(s)
- `next()` on the last row(s)
- `rolling_*()` on the first n-1 rows
- Division by zero
- `log()` of negative number
- Missing data after resample

NaN behavior:
- Arithmetic with NaN → NaN
- Comparison with NaN → false
- NaN in `where` → row excluded
- Aggregate functions ignore NaN (pandas default)
- `count()` counts non-NaN rows

---

## 9. Error Handling

### 9.1 Error Categories

| Error               | When                                      | Response                            |
|----------------------|-------------------------------------------|-------------------------------------|
| `UnknownColumn`     | Column name not in DataFrame              | Error with column name              |
| `UnknownFunction`   | Function name not recognized              | Error with function name            |
| `UnknownSession`    | Session not in instrument config          | Warning + use all data              |
| `UnknownSource`     | JOIN source doesn't exist                 | Error with source name              |
| `TypeError`         | Wrong argument type (e.g., `abs("text")`) | Error with expression               |
| `ParseError`        | Expression syntax is invalid              | Error with position info            |
| `ArityError`        | Wrong number of arguments                 | Error with expected vs actual count |
| `EmptyResult`       | Filter produced 0 rows                    | Return empty DataFrame / 0 / NaN   |

### 9.2 Error Response Format

```json
{
  "error": true,
  "error_type": "UnknownColumn",
  "message": "Column 'rnage' does not exist. Available: open, high, low, close, volume, range, gap",
  "expression": "rnage > 10",
  "step": "where"
}
```

### 9.3 Warnings

Non-fatal issues (query still executes):
- Unknown session → uses all data
- Empty result after filter → returns empty/zero
- NaN in aggregation → excluded from calculation

Warnings are included in result metadata, not as errors.

---

## 10. Interpreter Response

The interpreter returns a structured response object, not just a raw value. This serves multiple consumers with different needs.

### 10.1 Response Format

```json
{
  "result": 45.3,
  "metadata": {
    "rows": 4521,
    "period": "2006-01-01 — 2024-12-31",
    "session": "RTH",
    "from": "daily",
    "warnings": []
  },
  "table": [
    {"weekday": 0, "mean_range": 42.1},
    {"weekday": 1, "mean_range": 45.3}
  ],
  "query": {
    "from": "daily",
    "session": "RTH",
    "map": {"range": "high - low", "weekday": "dayofweek()"},
    "group_by": "weekday",
    "select": "mean(range)"
  }
}
```

### 10.2 Fields

| Field      | Type                          | Description                                                        |
|------------|-------------------------------|--------------------------------------------------------------------|
| `result`   | float \| int \| list[object]  | The computed answer. Scalar for ungrouped queries, list of row objects for grouped. |
| `metadata` | object                        | Execution context: how many source rows were used, period, session, timeframe, warnings. |
| `table`    | list[object] \| null          | Full result as array of row objects for UI display. null if result is a scalar. |
| `query`    | object                        | The original query that was executed. For debugging and UI display. |

**metadata fields:**

| Field      | Type         | Description                                   |
|------------|--------------|-----------------------------------------------|
| `rows`     | int          | Number of rows in the dataset after filtering (before aggregation) |
| `period`   | string       | Actual date range of the data used            |
| `session`  | string\|null | Session that was applied                      |
| `from`     | string       | Timeframe of the bars                         |
| `warnings` | list[string] | Non-fatal issues (unknown session, empty result, etc.) |

### 10.3 Who Sees What

**LLM** receives `result` + `metadata`. This is enough to formulate a human answer:

> "Средний RTH range NQ за все время — 45.3 пункта (на основе 4521 дневных баров)."

The LLM does **not** see `table`. This prevents hallucination — the LLM cannot misinterpret or selectively cite raw data. It gets the final number and context, nothing more.

**UI** receives `table` + `query`. The table is displayed as proof — the user can see and verify the data behind the answer. The UI can also render a graph from the table data. The `query` is shown for transparency (what was actually computed).

### 10.4 Result Types by Query Shape

| Query shape                 | `result` type      | `table`           |
|-----------------------------|--------------------|-------------------|
| No group_by, single select  | float or int       | null              |
| No group_by, list select    | object             | null              |
| group_by + select           | list[object]       | list[object]      |
| Error                       | (absent)           | (absent)          |

For errors, the response follows the error format from section 9.2 instead.

---

## 11. Validation

### 11.1 Approach

No separate validation layer. The interpreter is the single source of truth for what is valid.

**Lightweight JSON schema** catches structural garbage before execution:

| Check | What it catches |
|-------|----------------|
| Known fields only | `{"foo": "bar"}` → unknown field `foo` |
| `from` is one of 12 values | `"from": "3m"` → invalid timeframe |
| `limit` is a positive integer | `"limit": "ten"` → wrong type |
| `map` is an object | `"map": "range"` → wrong type |
| `select` is a string or list of strings | `"select": 42` → wrong type |
| `group_by` is a string or list of strings | `"group_by": true` → wrong type |
| `sort` is a string | `"sort": ["a", "b"]` → wrong type |
| `join` has `source` field | `"join": {}` → missing required field |

This is ~10 lines of schema definition. It rejects malformed queries instantly with a clear message.

### 11.2 Everything Else — Interpreter Handles It

All other errors are caught during execution:

- Unknown column → interpreter reaches MAP/WHERE, column not found → `UnknownColumn` error
- Unknown function → interpreter parses expression → `UnknownFunction` error
- Bad expression syntax → interpreter parses with AST → `ParseError`
- Session functions on minute timeframe → interpreter detects → `TypeError`
- Empty result → interpreter returns empty DataFrame / NaN

The interpreter already must handle all these cases (section 9). A separate validation layer would duplicate this logic and need to be kept in sync.

### 11.3 Error → Retry

When the interpreter returns an error, the LLM receives the error message and can generate a corrected query. This is the recovery mechanism — not prevention, but fast feedback:

```
LLM generates query → Interpreter returns error →
LLM sees error message → LLM generates corrected query → Interpreter executes
```

One retry is usually enough. The error messages are specific: they name the bad column, the unknown function, the parse position. The LLM has enough information to fix it.

---

## 12. Constraints

### What is NOT supported

1. **Arbitrary code** — Only expressions over columns using defined functions
2. **Loops / recursion** — No iteration, only the fixed execution pipeline
3. **Side effects** — Read-only, no writing to any source
4. **Subqueries** — No query-within-query
5. **Multiple sources** — One main source + optional JOIN
6. **User-defined functions** — Only built-in functions
7. **Unbounded windows** — Window size must be a fixed integer
8. **String operations** — No concat, split, regex on strings (only equality comparison)
9. **Cross-row references by condition** — No "find the row where X"
10. **Multiple JOINs** — At most one JOIN per query

### What IS supported via composition

Complex analyses that seem to need unsupported features can often be expressed by composing supported primitives:

- "What happens after NR7?" → Use `next()` in map + filter
- "Compare Monday vs Friday volume" → Use `group_by` + `where` with `in`
- "Average range on FOMC days" → Use `join` with events
- "SMA crossover" → Use two `rolling_mean()` in map + comparison in where

---

## 13. Examples

### 13.1 Basic — Count of daily bars

```json
{
  "from": "daily",
  "select": "count()"
}
```
→ int (e.g., `4521`)

### 13.2 Basic — Average daily volume

```json
{
  "from": "daily",
  "select": "mean(volume)"
}
```
→ float

### 13.3 Group — Volume by weekday

```json
{
  "from": "daily",
  "map": {"weekday": "dayofweek()"},
  "group_by": "weekday",
  "select": "mean(volume)",
  "sort": "mean_volume desc"
}
```
→ DataFrame with columns: weekday, mean_volume

### 13.4 Group — Monday vs Friday volume

```json
{
  "from": "daily",
  "map": {"weekday": "dayofweek()"},
  "where": "weekday in [0, 4]",
  "group_by": "weekday",
  "select": "mean(volume)"
}
```
→ DataFrame: 2 rows (0=Monday, 4=Friday)

### 13.5 Filter — Most volatile day of the week

```json
{
  "from": "daily",
  "map": {
    "range": "high - low",
    "weekday": "dayofweek()"
  },
  "group_by": "weekday",
  "select": "mean(range)",
  "sort": "mean_range desc",
  "limit": 1
}
```
→ DataFrame: 1 row with the most volatile weekday

### 13.6 Lag — Inside days count

An inside day: high < previous high AND low > previous low.

```json
{
  "from": "daily",
  "where": "high < prev(high) and low > prev(low)",
  "select": "count()"
}
```
→ int

### 13.7 Lag — Gap analysis

Gap: difference between today's open and yesterday's close.

```json
{
  "from": "daily",
  "map": {"gap": "open - prev(close)"},
  "where": "gap != 0",
  "select": ["count()", "mean(gap)", "mean(abs(gap))"]
}
```
→ DataFrame with count, mean_gap, mean_abs

### 13.8 Lag — Gap fill percentage

Gap fill: after a gap, does price return to previous close?

```json
{
  "from": "daily",
  "map": {
    "gap": "open - prev(close)",
    "gap_filled": "if(gap > 0, low <= prev(close), high >= prev(close))"
  },
  "where": "gap != 0",
  "select": "mean(gap_filled)"
}
```
→ float (proportion of gaps that filled, e.g., 0.72)

### 13.9 Window — NR7 (Narrowest Range of 7 days)

```json
{
  "from": "daily",
  "map": {
    "range": "high - low",
    "min_range_7": "rolling_min(range, 7)"
  },
  "where": "range == min_range_7",
  "select": "count()"
}
```
→ int (number of NR7 days)

### 13.10 Window + Lag — What happens after NR7

```json
{
  "from": "daily",
  "map": {
    "range": "high - low",
    "min_range_7": "rolling_min(range, 7)",
    "next_range": "next(range)"
  },
  "where": "range == min_range_7",
  "select": ["mean(next_range)", "mean(range)"]
}
```
→ DataFrame: mean range after NR7 vs mean NR7 range

### 13.11 Window — SMA crossover

Days where 20-day SMA crosses above 50-day SMA:

```json
{
  "from": "daily",
  "map": {
    "sma_20": "rolling_mean(close, 20)",
    "sma_50": "rolling_mean(close, 50)",
    "prev_sma_20": "prev(sma_20)",
    "prev_sma_50": "prev(sma_50)"
  },
  "where": "sma_20 > sma_50 and prev_sma_20 <= prev_sma_50",
  "select": "count()"
}
```
→ int (number of golden crosses)

Note: `map` columns are computed in order. `prev_sma_20` references `sma_20` which is computed first.

### 13.12 Session — RTH vs overnight range

```json
{
  "session": "RTH",
  "from": "daily",
  "map": {"range": "high - low"},
  "select": "mean(range)"
}
```
→ float (mean RTH daily range)

Run separately with `"session": "OVERNIGHT"` and compare.

### 13.13 Session — First hour average range

```json
{
  "session": "RTH_OPEN",
  "from": "daily",
  "map": {"range": "high - low"},
  "select": "mean(range)"
}
```
→ float

### 13.14 JOIN — Average range on FOMC days

```json
{
  "from": "daily",
  "join": {"source": "events", "filter": "event_id == 'fomc'"},
  "map": {"range": "high - low"},
  "select": "mean(range)"
}
```
→ float

### 13.15 JOIN — Volume on OPEX vs normal days

First query — OPEX days:
```json
{
  "from": "daily",
  "join": {"source": "events", "filter": "event_id == 'opex'"},
  "select": "mean(volume)"
}
```

Second query — all days:
```json
{
  "from": "daily",
  "select": "mean(volume)"
}
```

Compare the two results.

### 13.16 JOIN — Range by event type

```json
{
  "from": "daily",
  "join": {"source": "events", "filter": "event_impact == 'high'"},
  "map": {"range": "high - low"},
  "group_by": "event_id",
  "select": "mean(range)",
  "sort": "mean_range desc"
}
```
→ DataFrame: range per high-impact event type, sorted

### 13.17 Time — Hourly volume profile

```json
{
  "map": {"hour_of_day": "hour()"},
  "group_by": "hour_of_day",
  "select": "mean(volume)",
  "sort": "hour_of_day asc"
}
```
→ DataFrame: 24 rows with mean volume per hour

### 13.18 Time — Monthly seasonality

```json
{
  "from": "daily",
  "map": {
    "range": "high - low",
    "m": "month()"
  },
  "group_by": "m",
  "select": "mean(range)",
  "sort": "mean_range desc"
}
```
→ DataFrame: 12 rows, range per month

### 13.19 Complex — Outside days followed by continuation

Outside day (high > prev high AND low < prev low), check if next day continues:

```json
{
  "from": "daily",
  "map": {
    "is_outside": "high > prev(high) and low < prev(low)",
    "direction": "sign(close - open)",
    "next_direction": "next(sign(close - open))"
  },
  "where": "is_outside",
  "select": ["count()", "mean(direction)", "mean(next_direction)"]
}
```
→ DataFrame: count of outside days, their average direction, and next day's average direction

### 13.20 Complex — Year-over-year average range

```json
{
  "from": "daily",
  "map": {
    "range": "high - low",
    "yr": "year()"
  },
  "group_by": "yr",
  "select": ["mean(range)", "count()"],
  "sort": "yr asc"
}
```
→ DataFrame: yearly average range and bar count

---

## 14. Implementation Notes

These are non-normative notes for the interpreter implementor.

### 14.1 Expression Parser

Recommended: Python `ast` module with a whitelist evaluator.

- Parse expression string with `ast.parse(expr, mode='eval')`
- Walk the AST tree
- Whitelist allowed node types: `BinOp`, `Compare`, `BoolOp`, `UnaryOp`, `Call`, `Name`, `Constant`, `List`
- Map `Name` nodes to DataFrame columns
- Map `Call` nodes to registered functions
- Reject everything else

This provides safety (no arbitrary code execution) with zero dependencies.

### 14.2 Map Column Ordering

Map columns are computed in the order they appear in the JSON object. This allows later columns to reference earlier ones:

```json
{
  "map": {
    "range": "high - low",
    "prev_range": "prev(range)"
  }
}
```

`prev_range` works because `range` is computed first.

JSON object key ordering is guaranteed in Python 3.7+ dicts and in the JSON spec (in practice).

### 14.3 Aggregate Column Naming

When `select` contains aggregate expressions, the result column names follow this pattern:

| Expression            | Column name         |
|-----------------------|---------------------|
| `mean(range)`         | `mean_range`        |
| `sum(volume)`         | `sum_volume`        |
| `count()`             | `count`             |
| `std(close)`          | `std_close`         |
| `percentile(range, 0.95)` | `percentile_range` |
| `correlation(a, b)`   | `correlation_a_b`   |

Pattern: `{function}_{first_column_arg}` (additional args excluded from name).

### 14.4 Performance

For 18 years of minute data (~4.5M rows):
- Session filtering: fast (index-based time filter)
- Resample: fast (pandas built-in)
- Map: depends on expression complexity, typically fast
- Rolling window: O(n) with pandas rolling
- Group + aggregate: fast with pandas groupby

No special optimization needed for the current data size.
