# Data Pipeline

## Provider

FirstRate Data (firstratedata.com)
- 130 most active futures, updated daily by 11:45pm ET
- Subscription: €59.95/month, expires 2026-03-09
- License: derivative works allowed, no raw data redistribution
- Attribution required: "Data provided by FirstRate Data"

## API

Base: `https://firstratedata.com/api`
Auth: `userid=XMbX1O2zD0--j0RfUK-W9A`
Note: redirects to Backblaze B2, use `curl -L`

### Endpoints

**Data download:**
```
/api/data_file?type=futures&period={period}&timeframe={tf}&adjustment={adj}&userid=...
```
- period: `full` (all history), `month`, `week`, `day` (last trading day)
- timeframe: `1min`, `5min`, `30min`, `1hour`, `1day`
- adjustment: `contin_UNadj`, `contin_adj_ratio`, `contin_adj_absolute`

**Last update check:**
```
/api/last_update?type=futures&userid=...
```
Returns plain text date: `2026-02-10`

**Ticker listing:**
```
/api/ticker_listing?type=futures&userid=...
```

### Response format

Zip archive containing one txt per ticker:
- Daily: `{TICKER}_day_1day_continuous_UNadjusted.txt`
- 1min: `{TICKER}_day_1min_continuous_UNadjusted.txt`
- Full: `{TICKER}_full_1day_continuous_UNadjusted.txt`

### File format

- Daily (1day): `date,open,high,low,close,volume,OI` — 7 columns
- Intraday: `datetime,open,high,low,close,volume` — 6 columns
- Timezone: US Eastern
- Zero volume bars excluded

### Update timing

- `period=day` updates: available ~1:00 AM ET
- `period=full` archives: available ~2:00 AM ET

## What we download

We use **unadjusted continuous** (`contin_UNadj`) — raw traded prices, matches TradingView NQ1! style.

Two timeframes:
- **1day** — settlement close, matches TradingView SET mode within ~1 tick
- **1min** — for intraday queries, aggregated to 5m/15m/30m/1h on the fly

## Local storage

```
data/
  1d/futures/{SYMBOL}.parquet    — daily bars (from 1day txt)
  1m/futures/{SYMBOL}.parquet    — minute bars (from 1min txt)
  1d/stocks/{SYMBOL}.parquet     — (future)
  1m/stocks/{SYMBOL}.parquet     — (future)
```

Parquet format: `[timestamp, open, high, low, close, volume]`, compression=zstd.

## Symbol mapping

Provider symbols differ from TradingView:

| Provider | Our symbol | Name |
|----------|-----------|------|
| A6 | 6A | Australian Dollar |
| AD | 6C | Canadian Dollar |
| B | BRN | Brent Crude |
| B6 | 6B | British Pound |
| E1 | 6S | Swiss Franc |
| E6 | 6E | Euro FX |
| J1 | 6J | Japanese Yen |

Most other tickers match: NQ, ES, CL, GC, SI, ZW, ZC, etc.

## Known issues

### Contract roll divergence
Our provider rolls continuous contracts ~4 days before TradingView. This causes:
- ~4 bars per roll (4x/year = ~16 bars/year) with different OHLCV
- RSI diverges ~0.2 pts through Wilder's smoothing memory
- Window-based indicators (CCI, StochK, WilliamsR, MFI) unaffected when lookback doesn't cross roll

### Fix: custom continuous series (roadmap)

The provider API has a `futures_contract` endpoint that returns individual contracts
(e.g. NQZ2025, NQH2026). With these we can build our own continuous series:

1. Download individual contracts (`/api/futures_contract?contract_files=archive&timeframe=1day`)
2. Determine TradingView roll dates for each instrument (TV rolls on expiry week,
   our provider rolls ~4 days earlier)
3. Write a splicer that stitches contracts at TV roll dates
4. Result: 100% OHLCV match with TradingView, including roll days
5. Eliminates RSI/ATR divergence from Wilder's smoothing memory

Priority: after functions + prompt + server are done. Current 93% match is acceptable for launch.

### Settlement vs last-trade close
- 1d data: settlement close (matches TradingView SET mode within ~1 tick)
- 1m aggregated to daily: last-trade close (differs ~0.04% from settlement)
- This is why we need both 1d and 1m — can't derive daily from minutes

## Auto-update (implemented)

`scripts/update_data.py` — cron on server, daily at 1:15 AM ET (6:15 UTC), Mon-Fri.

```
1. GET last_update → check if new data available
2. GET period=day for 1day + 1min → zip archives
3. Extract our 31 tickers, apply symbol mapping
4. Validate new data (timestamps, OHLC > 0)
5. Append to parquet with dedup (atomic write: .tmp → rename)
6. PATCH Supabase instruments.data_end
7. Save state to .last_update
```

Server: `root@37.27.204.135:/opt/barb`, venv at `.venv-scripts/`, log at `/var/log/barb-update.log`.

See `docs/barb/data-update.md` for full architecture.

## Target tickers (31)

Provider ticker → our symbol (where different).

### Indices (6)
- ES — E-Mini S&P 500 (CME)
- NQ — E-Mini Nasdaq 100 (CME)
- YM — Dow Mini (CBOT)
- RTY — E-Mini Russell 2000 (CME)
- FDAX — DAX (EUREX)
- FESX — Euro Stoxx 50 (EUREX)

### Energy (5)
- CL — WTI Crude Oil (NYMEX)
- B → BRN — Brent Crude (ICE)
- NG — Natural Gas (NYMEX)
- RB — RBOB Gasoline (NYMEX)
- HO — Heating Oil (NYMEX)

### Metals (4)
- GC — Gold (CME)
- SI — Silver (CME)
- HG — Copper (CME)
- PL — Platinum (NYMEX)

### Currencies (6)
- E6 → 6E — Euro FX (CME)
- B6 → 6B — British Pound (CME)
- J1 → 6J — Japanese Yen (CME)
- A6 → 6A — Australian Dollar (CME)
- AD → 6C — Canadian Dollar (CME)
- E1 → 6S — Swiss Franc (CME)

### Treasuries (4)
- ZN — 10-Year T-Note (CBOT)
- ZF — 5-Year T-Note (CBOT)
- ZT — 2-Year T-Note (CBOT)
- US — 30-Year T-Bond (CBOT)

### Agriculture (5)
- ZC — Corn (CBOT)
- ZW — Wheat (CBOT)
- ZS — Soybeans (CBOT)
- KC — Coffee (ICE)
- CC — Cocoa (ICE)

### Crypto (1)
- BTC — Bitcoin (CME)
