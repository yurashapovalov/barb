# Pattern Detection

Detect price patterns using lag (prev/next) and rolling window functions.

## Key fields
- map: compute pattern indicators using prev(), rolling_min(), rolling_max(), etc.
- where: filter rows matching the pattern
- select: count or aggregate the matches

## Examples

Gap analysis (open vs previous close):
{"session": "RTH", "from": "daily", "map": {"gap": "open - prev(close)"}, "where": "gap != 0", "select": "mean(abs(gap))"}

NR7 — narrowest range of 7 days:
{"session": "RTH", "from": "daily", "map": {"range": "high - low", "min7": "rolling_min(range, 7)"}, "where": "range == min7", "select": "count()"}

Consecutive up days (streak):
{"session": "RTH", "from": "daily", "map": {"up": "close > open", "run": "streak(up)"}, "select": "max(run)"}

## Common mistakes
- prev(close) returns NaN for the first row — that's normal, NaN rows are excluded from where
- rolling_min(range, 7) needs two arguments: column and window size