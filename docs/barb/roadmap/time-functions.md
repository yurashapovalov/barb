# Time Functions — Simplification

## Problem

Model sees 11 time functions, 3 pairs doing the same thing in different formats:
- `dayofweek()` (0-4) / `dayname()` ("Monday")
- `month()` (1-12) / `monthname()` ("January")
- `hour()` (0-23) / `hour_range()` ("18:00-18:59")

More functions = more decisions = more errors. Model can't reliably choose between `hour()` and `hour_range()`.

## Key insight

An hour is a period of 60 minutes. `hour() = 18` means the period 18:00-18:59, not the instant 18:00. Same logic: `month() = 3` is March (all 31 days), `dayofweek() = 4` is Friday (the whole day). These are all periods, not points.

The display format should reflect this. The interpreter knows the function — it should format the output.

## Final function list

8 functions, one per concept, no pairs:

| Function | Returns | Display format | Use case |
|---|---|---|---|
| `year()` | 2024 | 2024 | Group/filter by year |
| `quarter()` | 1-4 | 1-4 | Group/filter by quarter |
| `month()` | 1-12 | January, February, ... | Group/filter by month |
| `date()` | date | 2024-01-15 | Group by day, always in output |
| `day_of_month()` | 1-31 | 1-31 | Filter: `day_of_month() <= 7` (first week) |
| `dayofweek()` | 0-4 | Monday, ..., Friday | Group/filter by day of week |
| `hour()` | 0-23 | 18:00-18:59 | Group/filter by hour (intraday) |
| `minute()` | 0-59 | 0-59 | Filter/group by minute (intraday) |

## Functions removed

- `dayname()` → auto-format of `dayofweek()`
- `monthname()` → auto-format of `month()`
- `hour_range()` → auto-format of `hour()`

## Functions renamed

- `day()` → `day_of_month()` — avoids confusion with `date()`

## How auto-formatting works

Interpreter has the map dict `{"col_name": "expression"}`. After filtering (on numbers), before output:

```python
DISPLAY_FORMATS = {
    "dayofweek()": lambda v: v.map({0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday"}),
    "month()": lambda v: v.map({1: "January", 2: "February", ...}),
    "hour()": lambda v: v.map(lambda h: f"{h:02d}:00-{h:02d}:59"),
}
```

For each column in map, if the expression matches a key in DISPLAY_FORMATS, format before output.

Filtering happens on numbers → correct comparisons. Display happens after → readable output.

## Impact

- Model: 8 functions instead of 11 — no pairs, no choice confusion
- Prompt: shorter, fewer decisions
- User: always readable output (no more `hr: 18`)
- Backward compat: keep removed functions in engine, remove from prompt
