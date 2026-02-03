# Barb Script Query Reference

## Query Format
JSON object with these fields (all optional):
- session: Trading session filter (RTH, ETH, OVERNIGHT, ASIAN, EUROPEAN, MORNING, AFTERNOON, RTH_OPEN, RTH_CLOSE)
- from: Timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly). Default: 1m
- period: Date range ("2024", "2024-03", "2024-01-01:2024-06-30", "last_year", "last_month", "last_week")
- map: Derived columns {name: "expression_string"}. Values MUST be strings.
- where: Row filter expression (boolean)
- group_by: Column to group by
- select: Aggregate expression. Default: count()
- sort: "column_name asc" or "column_name desc"
- limit: Max rows (positive integer)

## Execution Order
session → period → from → map → where → group_by → select → sort → limit

## Expressions
Arithmetic: +, -, *, /
Comparison: >, <, >=, <=, ==, !=
Boolean: and, or, not
Membership: weekday in [0, 1, 4]
Columns: open, high, low, close, volume (plus any map-defined columns)

## Functions

Scalar: abs(x), log(x), sqrt(x), sign(x), round(x, n), if(cond, then, else)
Lag: prev(col), prev(col, n), next(col), next(col, n)
Window: rolling_mean(col, n), rolling_sum(col, n), rolling_max(col, n), rolling_min(col, n), rolling_std(col, n), rolling_count(cond, n), ema(col, n)
Cumulative: cummax(col), cummin(col), cumsum(col)
Pattern: streak(cond), bars_since(cond), rank(col)
Aggregate: mean(col), sum(col), max(col), min(col), std(col), median(col), count(), percentile(col, p), correlation(col1, col2), last(col)
Time: dayofweek(), dayname(), hour(), month(), monthname(), year(), day(), quarter(), date()