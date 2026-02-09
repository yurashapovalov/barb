# NQ Data Notes

## Source
- `data/NQ.parquet` — minute bars, NQ E-Mini futures (CME)
- Range: 2008-01-02 to 2026-01-07
- ~5.9M rows, timestamps in US/Eastern (naive, no tz info)

## CME Session Structure
- Globex: 18:00 ET (prev day) → 17:00 ET (current day)
- Halt: 17:00–18:00 ET daily (no data)
- RTH: 09:30–16:15 ET

## Daily Aggregation
To match TradingView daily bars:
```python
shifted = df.copy()
shifted.index = shifted.index + pd.Timedelta(hours=6)
daily = shifted.resample('D').agg({
    'open': 'first', 'high': 'max',
    'low': 'min', 'close': 'last', 'volume': 'sum'
}).dropna()
```
Shift +6h maps 18:00→00:00 (session start = day boundary).

## Close Price Discrepancy
- **O/H/L match TradingView exactly**
- **Close differs by ~0.04%** (1–10 pts on ~25000)
- Cause: TradingView uses CME official settlement price, our data has last-trade-of-minute
- Settlement price is a calculated value (VWAP-based), not available in minute data
- For indicator tests: use ±1% tolerance on final values
- Verified on 2025-09-05 and 2025-12-17
