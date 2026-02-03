# Ranking

Sort results and take top/bottom N rows.

## Key fields
- map: compute the column to rank by
- group_by: optional grouping before ranking
- select: aggregate if grouped
- sort: "column desc" for top, "column asc" for bottom
- limit: how many rows to return

## Examples

Top 5 highest range days:
{"session": "RTH", "from": "daily", "map": {"range": "high - low"}, "sort": "range desc", "limit": 5}

Top 3 highest volume weekdays:
{"session": "RTH", "from": "daily", "map": {"weekday": "dayofweek()"}, "group_by": "weekday", "select": "mean(volume)", "sort": "mean_volume desc", "limit": 3}

Bottom 3 lowest volume months:
{"session": "RTH", "from": "daily", "map": {"m": "month()"}, "group_by": "m", "select": "mean(volume)", "sort": "mean_volume asc", "limit": 3}

## Common mistakes
- sort: "volume" — WRONG. Must specify direction: "volume desc" or "volume asc"
- Forgetting limit — without limit you get all rows sorted, not top N
