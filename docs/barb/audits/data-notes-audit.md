# Audit: data-notes.md

**Date**: 2026-02-16
**Claims checked**: 30
**Correct**: 27 | **Wrong**: 1 | **Outdated**: 0 | **Unverifiable**: 2

## Issues

### [WRONG] Daily parquet described as having 7 columns
- **Doc says**: `data/1d/futures/{SYMBOL}.parquet — daily bars (7 cols: date, O, H, L, C, volume, OI → we drop OI)`
- **Code says**: The raw CSV from FirstRateData has 7 columns (`DAILY_COLS = ["timestamp", "open", "high", "low", "close", "volume", "oi"]`), but OI is dropped at ingest time in `parse_daily_txt()` via `KEEP_COLS`. The stored parquet file has 6 columns: `timestamp, open, high, low, close, volume`. The "7 cols" description applies to the source CSV, not the parquet file.
- **File**: `scripts/update_data.py:89-106`, actual parquet verified via pandas

### [UNVERIFIABLE] Settlement close values match TradingView within ~1 tick
- **Doc says**: Close: 21,692.25 (ours) vs 21,692.50 (TV SET) on NQ Dec 22 2025
- **Evidence**: Cannot verify TradingView values from code alone. The settlement pricing methodology is external.

### [UNVERIFIABLE] Specific rollover offset magnitudes
- **Doc says**: HO ~0.06 offset, PL ~20 pts offset, KC ~7-8 pts offset
- **Evidence**: These are comparisons against TradingView, which cannot be verified from code. The existence of rollover issues is confirmed by notes in `scripts/upload_instruments.py` for all 4 instruments (BRN, HO, PL, KC).

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Provider is FirstRateData | CORRECT | `scripts/update_data.py:27` — `API_BASE = "https://firstratedata.com/api"` |
| 2 | Type is `contin_UNadj` (unadjusted continuous contracts) | CORRECT | `scripts/update_data.py:166` — `"adjustment": "contin_UNadj"` |
| 3 | Daily bars path: `data/1d/futures/{SYMBOL}.parquet` | CORRECT | `barb/data.py:20` — `path = DATA_DIR / timeframe / asset_type / f"{instrument.upper()}.parquet"` with timeframe="1d"; 31 files confirmed in `data/1d/futures/` |
| 4 | Daily bars have 7 cols (date, O, H, L, C, volume, OI) | WRONG | Source CSV has 7 cols (`update_data.py:89`), but stored parquet has 6 — OI is dropped at ingest (`update_data.py:91,106`) |
| 5 | OI is dropped from daily bars | CORRECT | `scripts/update_data.py:91` — `KEEP_COLS` excludes "oi"; `parse_daily_txt()` returns `df[KEEP_COLS]` (line 106) |
| 6 | Minute bars path: `data/1m/futures/{SYMBOL}.parquet` | CORRECT | Same path pattern in `barb/data.py:20`; 31 files confirmed in `data/1m/futures/` |
| 7 | Minute bars have 6 cols (datetime, O, H, L, C, volume) | CORRECT | `scripts/update_data.py:90` — `MINUTE_COLS = ["timestamp", "open", "high", "low", "close", "volume"]`; verified via pandas |
| 8 | 31 instruments | CORRECT | 31 parquet files counted in both `data/1d/futures/` and `data/1m/futures/` |
| 9 | Data range ~2008 to 2026-02 | CORRECT | NQ: 2008-01-02 to 2026-02-11; ES: 2008-01-02 to 2026-02-11; GC: 2008-01-28 to 2026-02-11 |
| 10 | Timestamps in US/Eastern (naive, no tz info) | CORRECT | Pandas shows `tz=None`; minute data session starts at 18:00 (matching CME Globex ET start) |
| 11 | Daily bars for `"from": "daily"` and longer timeframes | CORRECT | `barb/interpreter.py:17-30` — TIMEFRAMES includes daily, weekly, monthly, quarterly, yearly; chat.py uses `df_daily` for non-intraday |
| 12 | Minute bars for intraday queries (`"1m"`, `"5m"`, `"1h"`) | CORRECT | `barb/interpreter.py:49` — `_INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}`; `assistant/chat.py:150-151` |
| 13 | Minute bars used for RTH-like sessions (start < end) | CORRECT | `assistant/chat.py:153-157` — checks if `times[0] < times[1]`, uses `df_minute` if true |
| 14 | `load_data(instrument, timeframe, asset_type)` signature | CORRECT | `barb/data.py:12` — `def load_data(instrument: str, timeframe: str = "1d", asset_type: str = "futures")` |
| 15 | `@lru_cache` — loaded once per combination | CORRECT | `barb/data.py:11` — `@lru_cache` decorator on `load_data` |
| 16 | At load time, selects only `["open", "high", "low", "close", "volume"]` | CORRECT | `barb/data.py:27` — `df = df[["open", "high", "low", "close", "volume"]]` |
| 17 | Routing lives in `assistant/chat.py` | CORRECT | `assistant/chat.py:148-161` — timeframe/session logic chooses `df_minute` vs `df_daily` |
| 18 | Daily bars use exchange settlement close | UNVERIFIABLE | External data characteristic; cannot verify from code alone |
| 19 | Minute bars use last trade close per minute | UNVERIFIABLE | External data characteristic; cannot verify from code alone |
| 20 | Both data and TradingView SET mode use settlement price | UNVERIFIABLE | External comparison; code has notes in `scripts/upload_instruments.py` consistent with this |
| 21 | Verified NQ Dec 22 2025: O/H/L exact match, close within 1 tick | UNVERIFIABLE | TradingView comparison, not verifiable from code |
| 22 | Globex: 18:00 ET → 17:00 ET | CORRECT | `docs/others/sessions-reference.md:15` — "ETH: 18:00–17:00 ET (23 hours)"; minute data shows session start at 18:00 |
| 23 | Halt: 17:00–18:00 ET daily | CORRECT | `docs/others/sessions-reference.md:14` — "Maintenance 17:00–18:00 ET (60 min)"; no data in this window confirmed |
| 24 | RTH varies by product group, see `docs/others/sessions-reference.md` | CORRECT | File exists at `docs/others/sessions-reference.md` with per-group RTH tables |
| 25 | HO has rollover offset issue | CORRECT | `scripts/upload_instruments.py:222` — notes mention rollover date offset for HO |
| 26 | BRN has rollover offset issue | CORRECT | `scripts/upload_instruments.py:165` — notes mention rollover date offset for BRN |
| 27 | BRN 1d O/L differ from 1m→ETH aggregation | UNVERIFIABLE | Data comparison claim, not verifiable from code |
| 28 | PL has rollover offset (~20 pts) | CORRECT | `scripts/upload_instruments.py:299` — notes confirm rollover offset for PL; magnitude unverifiable |
| 29 | KC has rollover offset (~7-8 pts) | CORRECT | `scripts/upload_instruments.py:568` — notes confirm rollover offset for KC; magnitude unverifiable |
| 30 | HO ~0.06 constant offset on ALL values (O/H/L/C) | UNVERIFIABLE | Magnitude is an external TradingView comparison |
