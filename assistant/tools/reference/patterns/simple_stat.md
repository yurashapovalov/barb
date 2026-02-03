# Simple Statistics

Scalar result: one number from the whole dataset.

## Key fields
- session, from: define the data scope
- map: compute derived columns if needed
- select: aggregate function (mean, sum, count, etc.)

## Examples

Average daily range:
{"session": "RTH", "from": "daily", "map": {"range": "high - low"}, "select": "mean(range)"}

Total trading days:
{"session": "RTH", "from": "daily", "select": "count()"}

Average daily volume:
{"session": "RTH", "from": "daily", "select": "mean(volume)"}