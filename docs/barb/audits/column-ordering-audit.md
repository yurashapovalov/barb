# Audit: column-ordering.md

**Date**: 2026-02-16
**Claims checked**: 19
**Correct**: 19 | **Wrong**: 0 | **Outdated**: 0 | **Unverifiable**: 0

## Issues

No issues found. All claims match the current codebase.

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Intraday timeframes split timestamp into `date` + `time`; daily+ get only `date` | CORRECT | `barb/interpreter.py:509-514` — checks `timeframe in _INTRADAY_TIMEFRAMES`, adds `time` only for intraday |
| 2 | Intraday timeframes: 1m, 5m, 15m, 30m, 1h, 2h, 4h | CORRECT | `barb/interpreter.py:49` — `_INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}` |
| 3 | Daily+ timeframes: daily, weekly, monthly, quarterly, yearly | CORRECT | `barb/interpreter.py:17-30` — `TIMEFRAMES` set contains all listed values |
| 4 | Date format is `YYYY-MM-DD` (e.g. `2024-03-15`) | CORRECT | `barb/interpreter.py:511` — `ts.dt.strftime("%Y-%m-%d")` |
| 5 | Time format is `HH:MM` (e.g. `09:30`) | CORRECT | `barb/interpreter.py:513` — `ts.dt.strftime("%H:%M")` |
| 6 | Weekly/monthly/quarterly/yearly use pandas offsets W, ME, QE, YE (end of period) | CORRECT | `barb/interpreter.py:42-46` — `"weekly": "W"`, `"monthly": "ME"`, `"quarterly": "QE"`, `"yearly": "YE"` |
| 7 | Column priority: date → time → group keys → OHLC → volume → calculated → remaining | CORRECT | `barb/interpreter.py:521-555` — `_prepare_for_output` builds `ordered` list in exactly this sequence |
| 8 | OHLC standard order: open, high, low, close | CORRECT | `barb/interpreter.py:52` — `_OHLC_COLUMNS = ["open", "high", "low", "close"]` |
| 9 | Weekly example: `date \| open \| high \| low \| close \| volume \| drop_pct` | CORRECT | Follows from column priority: date first, OHLC, volume, then map column `drop_pct` |
| 10 | Intraday 1h example: `date \| time \| open \| high \| low \| close \| volume` | CORRECT | 1h is in `_INTRADAY_TIMEFRAMES`, so `time` is added after `date`, then OHLC + volume |
| 11 | Grouped example: `dow \| mean_gap` for `group_by: "dow", select: "mean(gap)"` | CORRECT | `_aggregate_col_name("mean(gap)")` returns `"mean_gap"` (`barb/interpreter.py:460-468`), group key becomes column via `reset_index()` |
| 12 | Grouped data has no `date`/`time` columns | CORRECT | `_group_aggregate` creates new DataFrame from aggregation results — no `timestamp` column exists, so `_prepare_for_output` never creates `date`/`time` |
| 13 | Implementation is in `barb/interpreter.py` → `_prepare_for_output()` | CORRECT | `barb/interpreter.py:493` — function exists at this location |
| 14 | Function signature: `def _prepare_for_output(df: pd.DataFrame, query: dict) -> pd.DataFrame:` | CORRECT | `barb/interpreter.py:493` — exact match |
| 15 | Docstring: `"""Prepare DataFrame for JSON output: split timestamp, order columns."""` | CORRECT | `barb/interpreter.py:494` — first line of docstring matches (full docstring has additional lines documenting column order priority) |
| 16 | Called in `_build_response()` before serialization | CORRECT | `barb/interpreter.py:612,617` — called on both `source_df` and `result` before `_serialize_records()` |
| 17 | OHLCV columns (`_PRESERVE_PRECISION`) preserve original precision | CORRECT | `barb/interpreter.py:55` — `_PRESERVE_PRECISION = {"open", "high", "low", "close", "volume"}`; `_serialize_records` skips rounding for these |
| 18 | All other float columns rounded to `CALCULATED_PRECISION = 4` | CORRECT | `barb/interpreter.py:58` — `CALCULATED_PRECISION = 4`; `_serialize_records:576,581` — `round(v, CALCULATED_PRECISION)` for non-preserved float columns |
| 19 | Rounding handled in `_serialize_records()` during DataFrame → JSON conversion | CORRECT | `barb/interpreter.py:558-585` — function converts records and applies rounding logic |
