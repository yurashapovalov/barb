# Group Analysis

Group data by a column, compute aggregates per group.

## Key fields
- map: create the grouping column (dayofweek(), month(), etc.)
- group_by: column name from map (NOT a function call)
- select: aggregate function (mean, sum, count, etc.)
- sort: order the result

## Examples

Volume by weekday:
{"session": "RTH", "from": "daily", "map": {"weekday": "dayofweek()"}, "group_by": "weekday", "select": "mean(volume)", "sort": "weekday asc"}

Range by month:
{"session": "RTH", "from": "daily", "map": {"range": "high - low", "m": "month()"}, "group_by": "m", "select": "mean(range)", "sort": "m asc"}

Count by year:
{"session": "RTH", "from": "daily", "map": {"y": "year()"}, "group_by": "y", "select": "count()", "sort": "y asc"}

## Common mistakes
- group_by: "dayofweek()" — WRONG. Create column in map first: map: {"weekday": "dayofweek()"}, group_by: "weekday"
- select: "dayofweek()" in group context — WRONG. Use func(column): mean(range), count()