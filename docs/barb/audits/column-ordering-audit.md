# Audit: column-ordering.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 9: "1m, 5m, 15m, 30m, 1h, 2h, 4h -> date + time"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:49` — `_INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}`; line 511-512: time column added only when `timeframe in _INTRADAY_TIMEFRAMES`

### Claim 2
- **Doc**: line 12: "daily, weekly, monthly, quarterly, yearly -> only date"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:49` — these timeframes are not in `_INTRADAY_TIMEFRAMES`, so the `time` column is never created; only `date` from line 510: `df["date"] = ts.dt.strftime("%Y-%m-%d")`

### Claim 3
- **Doc**: line 11: "date format 2024-03-15, time format 09:30"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:510` — `ts.dt.strftime("%Y-%m-%d")` and line 512: `ts.dt.strftime("%H:%M")`

### Claim 4
- **Doc**: line 14: "For weekly/monthly date is start of period"
- **Verdict**: WRONG
- **Evidence**: `barb/interpreter.py:42-45` — weekly uses `"W"` (week-ending Sunday), monthly uses `"ME"` (month-end), quarterly uses `"QE"` (quarter-end), yearly uses `"YE"` (year-end). Pandas default label is the **end** of the period, not the start.
- **Fix**: change "date is start of period" to "date is end of period"

### Claim 5
- **Doc**: line 21: "date -- always first"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:522-524` — `# 1. date` block: `if "date" in df.columns: ordered.append("date")`

### Claim 6
- **Doc**: line 22: "time -- only for intraday timeframes"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:526-528` — `# 2. time (if intraday)` block

### Claim 7
- **Doc**: line 23: "group keys -- if there is group_by"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:530-533` — `# 3. group keys` block iterates `group_cols`

### Claim 8
- **Doc**: line 24: "OHLC -- open, high, low, close (standard order)"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:52` — `_OHLC_COLUMNS = ["open", "high", "low", "close"]`; lines 535-538

### Claim 9
- **Doc**: line 25: "volume -- after OHLC"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:540-542` — `# 5. volume` block placed after the OHLC loop

### Claim 10
- **Doc**: line 26: "calculated -- columns from map, in declaration order"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:544-547` — `# 6. calculated columns (from map)` iterates `map_columns`

### Claim 11
- **Doc**: line 27: "remaining -- all others"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:549-552` — `# 7. remaining columns` block

### Claim 12
- **Doc**: line 65: "For grouped data date/time are not output -- these are aggregates"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:378-386` — `_group_aggregate` creates new DataFrame without timestamp

### Claim 13
- **Doc**: line 69: "barb/interpreter.py -> _prepare_for_output()"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:492` — `def _prepare_for_output(df: pd.DataFrame, query: dict) -> pd.DataFrame:`

### Claim 14
- **Doc**: line 72-73: function signature "def _prepare_for_output(df: pd.DataFrame, query: dict) -> pd.DataFrame"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:492` — exact match

### Claim 15
- **Doc**: line 76: "Called in _build_response() before serialization"
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:611` — `prepared = _prepare_for_output(source_df, query)` inside `_build_response`

### Claim 16
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:54-55` — `_PRESERVE_PRECISION` set for OHLCV columns; `_serialize_records` handles precision differently for OHLCV vs calculated columns
- **Fix**: add "Precision" section: OHLCV columns preserve original precision; calculated columns are rounded

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 14 |
| OUTDATED | 0 |
| WRONG | 1 |
| MISSING | 1 |
| UNVERIFIABLE | 0 |
| **Total** | **16** |
| **Accuracy** | **87%** |

## Verification

Date: 2026-02-15

### Claims 1-3 — CONFIRMED
### Claim 4 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: WRONG (confirmed)
- **Reason**: Doc says "дата начала периода" (start of period) but pandas offsets W, ME, QE, YE use end-of-period timestamps. Auditor correctly identified the error.
### Claims 5-16 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 15 |
| DISPUTED | 1 |
| INCONCLUSIVE | 0 |
| **Total** | **16** |
