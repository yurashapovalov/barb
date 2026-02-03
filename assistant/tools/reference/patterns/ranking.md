# Ranking

Sort results and take top/bottom N rows. Omit select to return rows as a table.

## Key fields
- map: compute the column to rank/filter by
- where: optional filter
- sort: "column desc" for top, "column asc" for bottom
- limit: how many rows to return
- select: ONLY if you need aggregation. Omit select to return individual rows.

## Examples

Top 5 highest range days (returns rows with all columns):
{"session": "RTH", "from": "daily", "map": {"range": "high - low"}, "sort": "range desc", "limit": 5}

Most volatile Fridays in 2025 (filter + sort, no select = rows):
{"session": "RTH", "from": "daily", "period": "2025", "map": {"range": "high - low", "weekday": "dayofweek()"}, "where": "weekday == 4", "sort": "range desc", "limit": 5}

All Fridays in 2025 (filter only, no select = rows):
{"session": "RTH", "from": "daily", "period": "2025", "map": {"weekday": "dayofweek()"}, "where": "weekday == 4"}

Top 3 highest volume weekdays (grouped = needs select):
{"session": "RTH", "from": "daily", "map": {"weekday": "dayofweek()"}, "group_by": "weekday", "select": "mean(volume)", "sort": "mean_volume desc", "limit": 3}

## Common mistakes
- sort: "volume" — WRONG. Must specify direction: "volume desc" or "volume asc"
- select: "range" — WRONG. select is for aggregate functions (mean, count, etc.). Omit select to return rows.
- select: "date,range" — WRONG. Cannot pick columns via select. Omit select — all columns are returned.
