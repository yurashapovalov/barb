# Expression Reference

Expressions are used in `add_column` and `filter_rows`.

## Base columns

open, high, low, close, volume

Plus any columns added with `add_column`.

## Operators

Arithmetic: `+`, `-`, `*`, `/`
Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
Boolean: `and`, `or`, `not`
Membership: `weekday in [0, 1, 4]`

## Functions

Scalar: `abs(x)`, `log(x)`, `sqrt(x)`, `sign(x)`, `round(x, n)`, `if(cond, then, else)`

Lag: `prev(col)`, `prev(col, n)`, `next(col)`, `next(col, n)`

Window: `rolling_mean(col, n)`, `rolling_sum(col, n)`, `rolling_max(col, n)`, `rolling_min(col, n)`, `rolling_std(col, n)`, `rolling_count(cond, n)`, `ema(col, n)`

Cumulative: `cummax(col)`, `cummin(col)`, `cumsum(col)`

Pattern: `streak(cond)`, `bars_since(cond)`, `rank(col)`

Time: `dayofweek()`, `dayname()`, `hour()`, `minute()`, `month()`, `monthname()`, `year()`, `day()`, `quarter()`, `date()`

## Common patterns

Range: `high - low`
Gap: `open - prev(close)`
Bullish day: `close > open`
Inside day: `high < prev(high) and low > prev(low)`
Change %: `(close - prev(close)) / prev(close) * 100`
NR7: `high - low == rolling_min(high - low, 7)`

## Notes

- `prev(close)` returns NaN for the first row — NaN rows are excluded from filters automatically
- `dayofweek()` returns 0=Monday, 1=Tuesday, ..., 4=Friday, 5=Saturday, 6=Sunday
- `if(cond, then, else)` works element-wise on columns
