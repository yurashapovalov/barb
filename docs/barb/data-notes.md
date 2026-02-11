# Data Notes

## Source
- Provider: FirstRateData (futures dataset)
- Type: `contin_UNadj` — unadjusted continuous contracts (front-month stitched)
- Two datasets per instrument:
  - `data/1d/{SYMBOL}.parquet` — daily bars (7 cols: date, O, H, L, C, volume, OI → we drop OI)
  - `data/1m/{SYMBOL}.parquet` — 1-minute bars (6 cols: datetime, O, H, L, C, volume)
- 31 instruments, range ~2008 to 2026-02
- Timestamps in US/Eastern (naive, no tz info)

## Two Datasets, Two Purposes
- **Daily bars** (`1d/`) — for `"from": "daily"` and longer timeframes (weekly, monthly)
- **Minute bars** (`1m/`) — for intraday queries (`"from": "1m"`, `"5m"`, `"1h"`, etc.)

Daily bars use **exchange settlement close** (official CME/COMEX/NYMEX/ICE price).
Minute bars use **last trade close** per minute.

## Settlement vs Last Trade

Provider daily bars use **settlement price** as close. This is the official exchange price:
- Calculated by the exchange (VWAP-based, sometimes committee-determined)
- Used for margin, mark-to-market, P&L calculations
- What traders see in professional terminals (CQG, Bloomberg, Interactive Brokers)
- Smoothed, not susceptible to last-second noise

TradingView shows **last trade** as close — the price of the last transaction before session end.

**Our daily close is more accurate than TradingView's.** Settlement is the professional standard.

### Measured differences (NQ, Dec 2025)
- O/H/L: exact match between provider 1d and 1m→ETH aggregation (and TradingView)
- Close: differs by 0.03–0.2% between settlement (ours) and last trade (TV)
- NQ Dec 22: settlement=25692.25, last trade=25700.25 (Δ=8 pts, 0.03%)
- NQ Dec 17: settlement=24898.75, last trade=24951.75 (Δ=53 pts, 0.21%)
- For indicator tests: use ±1% tolerance on final values to account for this

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
