# Filter + Count

Filter rows by condition. Use select for aggregation, or omit select to return matching rows.

## Key fields
- map: compute columns needed for filtering
- where: boolean expression (use == for equality, not =)
- select: aggregate on filtered rows. Omit to return rows as a table.

## Examples

Bullish day count:
{"session": "RTH", "from": "daily", "where": "close > open", "select": "count()"}

Inside days:
{"session": "RTH", "from": "daily", "where": "high < prev(high) and low > prev(low)", "select": "count()"}

Days with range above 200:
{"session": "RTH", "from": "daily", "map": {"range": "high - low"}, "where": "range > 200", "select": "count()"}

Fridays only:
{"session": "RTH", "from": "daily", "map": {"weekday": "dayofweek()"}, "where": "weekday == 4", "select": "count()"}

## Common mistakes
- where: "weekday = 4" — WRONG. Use == for comparison, not =
- where: "dayofweek() = 4" — WRONG on two levels: use ==, and dayofweek() returns a Series so it works but = is still wrong