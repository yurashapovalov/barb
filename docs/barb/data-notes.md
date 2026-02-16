# Data Notes

## Source
- Provider: FirstRateData (futures dataset)
- Type: `contin_UNadj` — unadjusted continuous contracts (front-month stitched)
- Two datasets per instrument:
  - `data/1d/futures/{SYMBOL}.parquet` — daily bars (7 cols: date, O, H, L, C, volume, OI → we drop OI)
  - `data/1m/futures/{SYMBOL}.parquet` — 1-minute bars (6 cols: datetime, O, H, L, C, volume)
- 31 instruments, range ~2008 to 2026-02
- Timestamps in US/Eastern (naive, no tz info)

## Two Datasets, Two Purposes
- **Daily bars** (`1d/`) — for `"from": "daily"` and longer timeframes (weekly, monthly, quarterly, yearly)
- **Minute bars** (`1m/`) — for intraday queries (`"from": "1m"`, `"5m"`, `"1h"`, etc.) and session-specific daily queries (RTH-like sessions where start < end use minute data)

`barb/data.py` loads data via `load_data(instrument, timeframe, asset_type)` — `@lru_cache`, loaded once per combination. At load time, selects only `["open", "high", "low", "close", "volume"]` columns. Routing (which dataset for which query) lives in `assistant/chat.py`.

Daily bars use **exchange settlement close** (official CME/COMEX/NYMEX/ICE price).
Minute bars use **last trade close** per minute.

## Settlement Close

Both our data and TradingView (SET mode) use **settlement price** as daily close.

Settlement price:
- Calculated by the exchange (VWAP-based, sometimes committee-determined)
- Used for margin, mark-to-market, P&L calculations
- What traders see in professional terminals (CQG, Bloomberg, Interactive Brokers)

TradingView has a "SET" toggle (bottom-right) to switch between settlement and last trade.
In SET mode, our data matches TradingView within ~1 tick.

### Verified (NQ, Dec 22 2025)
- O/H/L: exact match
- Close: 25,692.25 (ours) vs 25,692.50 (TV SET) — Δ=0.25, one tick (0.001%)
- Indicator impact: negligible

## CME Session Structure
- Globex: 18:00 ET (prev day) → 17:00 ET (current day)
- Halt: 17:00–18:00 ET daily (no data)
- RTH varies by product group (see `docs/others/sessions-reference.md`)

## Known Issues

### HO (Heating Oil) — rollover offset
Provider and TradingView use different rollover dates for continuous contract.
Result: ~0.06 constant offset on ALL values (O/H/L/C). Specs (pv, tick) are correct.

### BRN (Brent Crude) — rollover offset
Same issue as HO. Provider 1d O/L differ from 1m→ETH aggregation,
suggesting different continuous contract construction.

### PL (Platinum) — rollover offset
Same issue as HO/BRN. All OHLC differ from TV by ~20 pts constant offset.

### KC (Coffee) — rollover offset
Same issue. All OHLC differ from TV by ~7-8 pts constant offset.
