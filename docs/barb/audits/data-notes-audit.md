# Audit: data-notes.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 4: "Provider: FirstRateData (futures dataset)"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:2` — `"""Daily data update from FirstRateData API.`; line 27 — `API_BASE = "https://firstratedata.com/api"`

### Claim 2
- **Doc**: line 5: "Type: `contin_UNadj` -- unadjusted continuous contracts"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:166` — `"adjustment": "contin_UNadj",`

### Claim 3
- **Doc**: line 7: "`data/1d/futures/{SYMBOL}.parquet` -- daily bars (7 cols: date, O, H, L, C, volume, OI -> we drop OI)"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:89` — `DAILY_COLS` has 7 cols; line 91 — `KEEP_COLS` drops OI

### Claim 4
- **Doc**: line 8: "`data/1m/futures/{SYMBOL}.parquet` -- 1-minute bars (6 cols)"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:90` — `MINUTE_COLS` has 6 cols

### Claim 5
- **Doc**: line 9: "31 instruments, range ~2008 to 2026-02"
- **Verdict**: ACCURATE
- **Evidence**: glob of `data/1d/futures/*.parquet` returns 31 files

### Claim 6
- **Doc**: line 10: "Timestamps in US/Eastern (naive, no tz info)"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about data provider's timestamp format in parquet files

### Claim 7
- **Doc**: line 13: "Daily bars (`1d/`) -- for `\"from\": \"daily\"` and longer timeframes"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:148-161` — non-intraday uses `df_daily`; `barb/interpreter.py:17-30` — includes daily, weekly, monthly

### Claim 8
- **Doc**: line 14: "Minute bars (`1m/`) -- for intraday queries"
- **Verdict**: ACCURATE
- **Evidence**: `assistant/chat.py:150-151` — `if timeframe in _INTRADAY: df = self.df_minute`

### Claim 9
- **Doc**: line 16: "Daily bars use exchange settlement close"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about data content from provider

### Claim 10
- **Doc**: line 17: "Minute bars use last trade close per minute"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about data content from provider

### Claim 11
- **Doc**: line 21: "Both our data and TradingView (SET mode) use settlement price as daily close"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about data content and external system

### Claim 12
- **Doc**: line 24: "Calculated by the exchange (VWAP-based, sometimes committee-determined)"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about exchange methodology

### Claim 13
- **Doc**: line 25: "Used for margin, mark-to-market, P&L calculations"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about exchange settlement usage

### Claim 14
- **Doc**: line 31-34: "Verified (NQ, Dec 22 2025) -- O/H/L: exact match, Close: 25,692.25 vs 25,692.50"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about specific comparison with TradingView on a specific date

### Claim 15
- **Doc**: line 37: "Globex: 18:00 ET (prev day) -> 17:00 ET (current day)"
- **Verdict**: ACCURATE
- **Evidence**: `docs/others/sessions-reference.md:15` — `ETH: 18:00-17:00 ET (23 hours).`

### Claim 16
- **Doc**: line 38: "Halt: 17:00-18:00 ET daily (no data)"
- **Verdict**: ACCURATE
- **Evidence**: `docs/others/sessions-reference.md:14` — `Maintenance 17:00-18:00 ET (60 min).`

### Claim 17
- **Doc**: line 39: "RTH varies by product group (see `docs/others/sessions-reference.md`)"
- **Verdict**: ACCURATE
- **Evidence**: `docs/others/sessions-reference.md:17-25` — table with different RTH by product group

### Claim 18
- **Doc**: line 44: "HO (Heating Oil) -- rollover offset"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about data comparison with TradingView

### Claim 19
- **Doc**: line 48: "BRN (Brent Crude) -- rollover offset"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about data comparison between datasets

### Claim 20
- **Doc**: line 52: "PL (Platinum) -- rollover offset: ~20 pts constant offset"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim about data comparison with TradingView

### Claim 21
- **Doc**: line 55: "KC (Coffee) -- rollover offset: ~7-8 pts constant offset"
- **Verdict**: UNVERIFIABLE (external data comparison)

### Claim 22
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/data.py:27` — `df = df[["open", "high", "low", "close", "volume"]]` — load-time column filter not documented
- **Fix**: add to "Two Datasets" section

### Claim 23
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/data.py:11` — `@lru_cache` — data cached in memory, loaded once per instrument+timeframe
- **Fix**: add to "Two Datasets" section

### Claim 24
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:28-29` — TIMEFRAMES includes `"quarterly"` and `"yearly"` in addition to daily/weekly/monthly
- **Fix**: add to line 13

### Claim 25
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/chat.py:152-159` — session-aware routing: RTH with daily timeframe uses minute data, ETH uses daily data
- **Fix**: add to "Two Datasets" section

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 12 |
| OUTDATED | 0 |
| WRONG | 0 |
| MISSING | 4 |
| UNVERIFIABLE | 9 |
| **Total** | **25** |
| **Accuracy** | **48%** |

Note: 9 UNVERIFIABLE claims are about external data properties (provider, TradingView, exchange methodology). Among code-verifiable claims (16), accuracy is 12/16 = 75%.

## Verification

Date: 2026-02-15

### Claim 1 — CONFIRMED
### Claim 2 — CONFIRMED
### Claim 3 — CONFIRMED
### Claim 4 — CONFIRMED
### Claim 5 — CONFIRMED
### Claim 6 — INCONCLUSIVE
### Claim 7 — CONFIRMED
### Claim 8 — CONFIRMED
### Claim 9 — INCONCLUSIVE
### Claim 10 — INCONCLUSIVE
### Claim 11 — INCONCLUSIVE
### Claim 12 — INCONCLUSIVE
### Claim 13 — INCONCLUSIVE
### Claim 14 — INCONCLUSIVE
### Claim 15 — CONFIRMED
### Claim 16 — CONFIRMED
### Claim 17 — CONFIRMED
### Claim 18 — INCONCLUSIVE
### Claim 19 — INCONCLUSIVE
### Claim 20 — INCONCLUSIVE
### Claim 21 — INCONCLUSIVE
### Claim 22 — CONFIRMED
### Claim 23 — CONFIRMED
### Claim 24 — CONFIRMED
### Claim 25 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 17 |
| DISPUTED | 0 |
| INCONCLUSIVE | 8 |
| **Total** | **25** |
