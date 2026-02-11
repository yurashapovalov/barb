# Supabase Instruments — Complete Data for All 31 Tickers

All sessions in ET. Status: existing (needs update), new (needs insert).

---

## Part 1: Existing — need updates (11 instruments)

### NQ — Nasdaq 100 E-Mini ✅
**Status**: update config
**TV verified**: pv=20, tick=0.25, CME, USD
```json
{
  "symbol": "NQ",
  "name": "E-Mini Nasdaq 100",
  "exchange": "CME",
  "category": "index",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "options"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:30", "16:15"]},
    "tick_size": 0.25,
    "tick_value": 5.0,
    "point_value": 20
  }
}
```

### ES — E-mini S&P 500 ✅
**Status**: update config (add tick_value)
**TV verified**: pv=50, tick=0.25, CME, USD
```json
{
  "symbol": "ES",
  "name": "E-mini S&P 500",
  "exchange": "CME",
  "category": "index",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "options"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:30", "16:15"]},
    "tick_size": 0.25,
    "tick_value": 12.50,
    "point_value": 50
  }
}
```

### 6A — Australian Dollar ✅
**Status**: update config (fix RTH, remove sub-sessions)
**TV verified**: pv=100000, tick=0.00005, CME, USD
```json
{
  "symbol": "6A",
  "name": "Australian Dollar Futures",
  "exchange": "CME",
  "category": "currency",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "16:00"]},
    "tick_size": 0.00005,
    "tick_value": 5.0,
    "point_value": 100000
  }
}
```

### 6B — British Pound ✅
**Status**: update config (fix RTH)
**TV verified**: pv=62500, tick=0.0001, CME, USD
```json
{
  "symbol": "6B",
  "name": "British Pound Futures",
  "exchange": "CME",
  "category": "currency",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "16:00"]},
    "tick_size": 0.0001,
    "tick_value": 6.25,
    "point_value": 62500
  }
}
```

### 6C — Canadian Dollar ✅
**Status**: update config (fix RTH, remove sub-sessions)
**TV verified**: pv=100000, tick=0.00005, CME, USD
```json
{
  "symbol": "6C",
  "name": "Canadian Dollar Futures",
  "exchange": "CME",
  "category": "currency",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "16:00"]},
    "tick_size": 0.00005,
    "tick_value": 5.0,
    "point_value": 100000
  }
}
```

### 6E — Euro FX ✅
**Status**: update config (fix RTH)
**TV verified**: pv=125000, tick=0.00005, CME, USD
```json
{
  "symbol": "6E",
  "name": "Euro FX Futures",
  "exchange": "CME",
  "category": "currency",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "16:00"]},
    "tick_size": 0.00005,
    "tick_value": 6.25,
    "point_value": 125000
  }
}
```

### CL — WTI Crude Oil ✅
**Status**: ok
**TV verified**: pv=1000, tick=0.01, NYMEX, USD
```json
{
  "symbol": "CL",
  "name": "WTI Crude Oil Futures",
  "exchange": "NYMEX",
  "category": "energy",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "oil"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:00", "14:30"]},
    "tick_size": 0.01,
    "tick_value": 10.0,
    "point_value": 1000
  }
}
```

### BRN — Brent Crude ✅
**Status**: update config (fix ETH + RTH)
**TV verified**: pv=1000, tick=0.01, ICEEUR, USD
```json
{
  "symbol": "BRN",
  "name": "Brent Crude Oil Futures",
  "exchange": "ICEEUR",
  "category": "energy",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "oil"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": "Unadjusted continuous contract (actual historic traded prices, no adjustments). Rollover date may differ from other platforms, causing a constant OHLC offset. Indicators are correct.",
  "config": {
    "sessions": {"ETH": ["20:00", "17:00"], "RTH": ["03:00", "14:30"]},
    "tick_size": 0.01,
    "tick_value": 10.0,
    "point_value": 1000
  }
}
```
**Changes**: fix ETH 20:00-18:00 → 20:00-17:00, fix RTH 09:30-18:00 → 03:00-14:30

### CC — Cocoa ✅
**Status**: update config (fix sessions)
**TV verified**: pv=10, tick=1, ICEUS, USD
```json
{
  "symbol": "CC",
  "name": "Cocoa Futures",
  "exchange": "ICEUS",
  "category": "agriculture",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "config": {
    "sessions": {"ETH": ["04:45", "13:25"]},
    "tick_size": 1,
    "tick_value": 10,
    "point_value": 10
  }
}
```
**Changes**: remove RTH (ETH = full trading day), fix ETH end 13:31 → 13:25
**Note**: TV shows 13:31, minute data shows last bar at 13:25

### BTC — Bitcoin ✅
**Status**: update config (add crypto events)
**TV verified**: pv=5, tick=5, CME, USD
```json
{
  "symbol": "BTC",
  "name": "Bitcoin Futures",
  "exchange": "CME",
  "category": "crypto",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "crypto"],
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:30", "16:00"]},
    "tick_size": 5,
    "tick_value": 25,
    "point_value": 5
  }
}
```
**Changes**: add crypto events

### GC — Gold ✅
**Status**: fix image_url format
**TV verified**: pv=100, tick=0.1, COMEX, USD
```json
{
  "symbol": "GC",
  "name": "Gold Futures",
  "exchange": "COMEX",
  "category": "metals",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "13:30"]},
    "tick_size": 0.1,
    "tick_value": 10,
    "point_value": 100
  }
}
```


### Indices

#### YM — Dow Mini ✅
**TV verified**: pv=5, tick=1, CBOT, USD
```json
{
  "symbol": "YM",
  "name": "E-mini Dow ($5)",
  "exchange": "CBOT",
  "category": "index",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "options"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:30", "16:15"]},
    "tick_size": 1,
    "tick_value": 5,
    "point_value": 5
  }
}
```

#### RTY — Russell 2000 E-mini ✅
**TV verified**: pv=50, tick=0.1, CME, USD
```json
{
  "symbol": "RTY",
  "name": "E-mini Russell 2000",
  "exchange": "CME",
  "category": "index",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "options"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:30", "16:15"]},
    "tick_size": 0.1,
    "tick_value": 5,
    "point_value": 50
  }
}
```

#### FDAX — DAX Futures ✅
**TV verified**: pv=25, tick=1, EUREX, EUR
```json
{
  "symbol": "FDAX",
  "name": "DAX Futures",
  "exchange": "EUREX",
  "category": "index",
  "currency": "EUR",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["19:15", "16:00"], "RTH": ["03:00", "11:30"]},
    "tick_size": 1,
    "tick_value": 25,
    "point_value": 25
  }
}
```
**Note**: TV shows tick=1 (was 0.5 in original entry). tick_value updated 12.5 → 25.

#### FESX — Euro Stoxx 50 Futures ✅
**TV verified**: pv=10, tick=1, EUREX, EUR
```json
{
  "symbol": "FESX",
  "name": "Euro Stoxx 50 Index Futures",
  "exchange": "EUREX",
  "category": "index",
  "currency": "EUR",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["19:15", "16:00"], "RTH": ["03:00", "11:30"]},
    "tick_size": 1,
    "tick_value": 10,
    "point_value": 10
  }
}
```

### Energy

#### NG — Natural Gas ✅
**TV verified**: pv=10000, tick=0.001, NYMEX, USD
```json
{
  "symbol": "NG",
  "name": "Henry Hub Natural Gas Futures",
  "exchange": "NYMEX",
  "category": "energy",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "oil"],
  "data_start": "2008-02-25",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:00", "14:30"]},
    "tick_size": 0.001,
    "tick_value": 10,
    "point_value": 10000
  }
}
```

#### RB — RBOB Gasoline ✅
**TV verified**: pv=42000, tick=0.0001, NYMEX, USD
```json
{
  "symbol": "RB",
  "name": "RBOB Gasoline Futures",
  "exchange": "NYMEX",
  "category": "energy",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "oil"],
  "data_start": "2008-02-11",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:00", "14:30"]},
    "tick_size": 0.0001,
    "tick_value": 4.20,
    "point_value": 42000
  }
}
```

#### HO — Heating Oil (NY Harbor ULSD) ✅
**TV verified**: pv=42000, tick=0.0001, NYMEX, USD
**⚠️ Data**: continuous rollover differs from TV (~0.06 contango offset). Specs correct, OHLC won't match 1:1.
```json
{
  "symbol": "HO",
  "name": "NY Harbor ULSD Futures",
  "exchange": "NYMEX",
  "category": "energy",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro", "oil"],
  "data_start": "2008-02-15",
  "data_end": "2026-02-06",
  "notes": "Unadjusted continuous contract (actual historic traded prices, no adjustments). Rollover date may differ from other platforms, causing a constant OHLC offset. Indicators are correct.",
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:00", "14:30"]},
    "tick_size": 0.0001,
    "tick_value": 4.20,
    "point_value": 42000
  }
}
```

### Metals

#### SI — Silver ✅
**TV verified**: pv=5000, tick=0.005, COMEX, USD
```json
{
  "symbol": "SI",
  "name": "Silver Futures",
  "exchange": "COMEX",
  "category": "metals",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "13:30"]},
    "tick_size": 0.005,
    "tick_value": 25,
    "point_value": 5000
  }
}
```

#### HG — Copper ✅
**TV verified**: pv=25000, tick=0.0005, COMEX, USD
```json
{
  "symbol": "HG",
  "name": "Copper Futures",
  "exchange": "COMEX",
  "category": "metals",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "13:30"]},
    "tick_size": 0.0005,
    "tick_value": 12.50,
    "point_value": 25000
  }
}
```

#### PL — Platinum ✅
**TV verified**: pv=50, tick=0.1, NYMEX, USD
**Data mismatch**: all OHLC differ by ~20 pts (rollover date difference, same issue as HO/BRN)
```json
{
  "symbol": "PL",
  "name": "Platinum Futures",
  "exchange": "NYMEX",
  "category": "metals",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": "Unadjusted continuous contract (actual historic traded prices, no adjustments). Rollover date may differ from other platforms, causing a constant OHLC offset. Indicators are correct.",
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "13:30"]},
    "tick_size": 0.1,
    "tick_value": 5,
    "point_value": 50
  }
}
```

### Currencies

#### 6J — Japanese Yen ✅
**TV verified**: pv=12500000, tick=0.0000005, CME, USD
```json
{
  "symbol": "6J",
  "name": "Japanese Yen Futures",
  "exchange": "CME",
  "category": "currency",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "16:00"]},
    "tick_size": 0.0000005,
    "tick_value": 6.25,
    "point_value": 12500000
  }
}
```

#### 6S — Swiss Franc ✅
**TV verified**: pv=125000, tick=0.00005, CME, USD
```json
{
  "symbol": "6S",
  "name": "Swiss Franc Futures",
  "exchange": "CME",
  "category": "currency",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "16:00"]},
    "tick_size": 0.00005,
    "tick_value": 6.25,
    "point_value": 125000
  }
}
```
**Note**: TV shows tick=0.00005 (was 0.0001 in original entry). tick_value updated 12.50 → 6.25.

### Treasuries

#### ZN — 10-Year T-Note ✅
**TV verified**: pv=1000, tick=1/2 of 1/32 (0.015625), CBOT, USD
```json
{
  "symbol": "ZN",
  "name": "10-Year T-Note Futures",
  "exchange": "CBOT",
  "category": "treasury",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "15:00"]},
    "tick_size": 0.015625,
    "tick_value": 15.625,
    "point_value": 1000
  }
}
```
**Note**: tick = 1/64 point. Price quoted in points (e.g., 112.109375 = 112-07/64).

#### ZF — 5-Year T-Note ✅
**TV verified**: pv=1000, tick=1/4 of 1/32 (0.0078125), CBOT, USD
```json
{
  "symbol": "ZF",
  "name": "5-Year T-Note Futures",
  "exchange": "CBOT",
  "category": "treasury",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "15:00"]},
    "tick_size": 0.0078125,
    "tick_value": 7.8125,
    "point_value": 1000
  }
}
```
**Note**: tick = 1/128 point.

#### ZT — 2-Year T-Note ✅
**TV verified**: pv=2000, tick=1/8 of 1/32 (0.00390625), CBOT, USD
```json
{
  "symbol": "ZT",
  "name": "2-Year T-Note Futures",
  "exchange": "CBOT",
  "category": "treasury",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "15:00"]},
    "tick_size": 0.00390625,
    "tick_value": 7.8125,
    "point_value": 2000
  }
}
```
**Note**: TV shows tick=1/256 (was 1/128 in original entry). tick_size 0.0078125 → 0.00390625, tick_value 15.625 → 7.8125.

#### US — 30-Year T-Bond ✅
**TV verified**: pv=1000, tick=1/32 (0.03125), CBOT, USD. TV symbol = **ZB1!** (our symbol = US)
```json
{
  "symbol": "US",
  "name": "30-Year T-Bond Futures",
  "exchange": "CBOT",
  "category": "treasury",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["18:00", "17:00"], "RTH": ["08:20", "15:00"]},
    "tick_size": 0.03125,
    "tick_value": 31.25,
    "point_value": 1000
  }
}
```
**Note**: tick = 1/32 point. TV symbol is ZB, provider symbol is US.

### Agriculture

#### ZC — Corn ✅
**TV verified**: pv=5000 (USX), tick=2/8 (0.25), CBOT. TV currency=USX, we use USD: pv=50
```json
{
  "symbol": "ZC",
  "name": "Corn Futures",
  "exchange": "CBOT",
  "category": "agriculture",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-02-19",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["20:00", "14:20"], "RTH": ["09:30", "14:20"]},
    "tick_size": 0.25,
    "tick_value": 12.50,
    "point_value": 50
  }
}
```
**Note**: 5,000 bushels, quoted in cents/bushel. TV shows pv=5000 in USX (cents), we store pv=50 in USD.

#### ZW — Wheat ✅
**TV verified**: pv=5000 (USX), tick=2/8 (0.25), CBOT. TV currency=USX, we use USD: pv=50
```json
{
  "symbol": "ZW",
  "name": "Wheat Futures",
  "exchange": "CBOT",
  "category": "agriculture",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["20:00", "14:20"], "RTH": ["09:30", "14:20"]},
    "tick_size": 0.25,
    "tick_value": 12.50,
    "point_value": 50
  }
}
```

#### ZS — Soybeans ✅
**TV verified**: pv=5000 (USX), tick=2/8 (0.25), CBOT. TV currency=USX, we use USD: pv=50
```json
{
  "symbol": "ZS",
  "name": "Soybean Futures",
  "exchange": "CBOT",
  "category": "agriculture",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-03-03",
  "data_end": "2026-02-06",
  "notes": null,
  "config": {
    "sessions": {"ETH": ["20:00", "14:20"], "RTH": ["09:30", "14:20"]},
    "tick_size": 0.25,
    "tick_value": 12.50,
    "point_value": 50
  }
}
```

#### KC — Coffee ✅
**TV verified**: pv=37500 (USX), tick=0.05, ICEUS. TV currency=USX, we use USD: pv=375
**Data mismatch**: all OHLC differ by ~7-8 pts (rollover date difference, same issue as HO/BRN/PL)
```json
{
  "symbol": "KC",
  "name": "Coffee C Futures",
  "exchange": "ICEUS",
  "category": "agriculture",
  "currency": "USD",
  "type": "futures",
  "default_session": "ETH",
  "events": ["macro"],
  "data_start": "2008-01-02",
  "data_end": "2026-02-06",
  "notes": "Unadjusted continuous contract (actual historic traded prices, no adjustments). Rollover date may differ from other platforms, causing a constant OHLC offset. Indicators are correct.",
  "config": {
    "sessions": {"ETH": ["04:15", "13:25"]},
    "tick_size": 0.05,
    "tick_value": 18.75,
    "point_value": 375
  }
}
```
**Note**: 37,500 lbs, cents/lb. No separate RTH (short session = full trading day).

---

## Part 3: Logos

### Have logo (uploaded to Supabase)
6A, 6B (as B6.svg), 6C, 6E, BRN, BTC, CC, CL, ES, GC, NQ

### Need logo (20 instruments)
6J, 6S, FDAX, FESX, HG, HO, KC, NG, PL, RB, RTY, SI, US, YM, ZC, ZF, ZN, ZS, ZT, ZW

---

## Part 4: Checklist

- [ ] Update NQ config (simplify sessions, add tick_value)
- [ ] Update ES config (add tick_value)
- [ ] Update 6A config (fix RTH)
- [ ] Update 6B config (fix RTH)
- [ ] Update 6C config (fix RTH)
- [ ] Update 6E config (fix RTH)
- [ ] Update BRN config (fix ETH + RTH)
- [ ] Update CC config (fix times)
- [ ] Fix GC image_url format
- [ ] Insert YM
- [ ] Insert RTY
- [ ] Insert FDAX
- [ ] Insert FESX
- [ ] Insert NG
- [ ] Insert RB
- [ ] Insert HO
- [ ] Insert SI
- [ ] Insert HG
- [ ] Insert PL
- [ ] Insert 6J
- [ ] Insert 6S
- [ ] Insert ZN
- [ ] Insert ZF
- [ ] Insert ZT
- [ ] Insert US
- [ ] Insert ZC
- [ ] Insert ZW
- [ ] Insert ZS
- [ ] Insert KC
- [ ] Create + upload 20 logos
