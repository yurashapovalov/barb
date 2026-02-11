# Session Reference — RTH by Product Group

All times in US/Eastern (ET). RTH = historical pit/floor hours, now industry standard.

## Sources

- **ETH & maintenance**: verified from minute data volume analysis (exact)
- **RTH**: historical pit hours, confirmed by CME contract specs + volume analysis
- **Grains RTH**: confirmed from CME holiday schedule (08:30–13:20 CT = 09:30–14:20 ET)
- TradingView does NOT define separate RTH for futures — only electronic session (ETH)

## CME Group (CME, CBOT, NYMEX, COMEX)

All use Globex platform. Maintenance 17:00–18:00 ET (60 min).
ETH: 18:00–17:00 ET (23 hours).

| Group | Products | RTH (ET) | Origin |
|-------|----------|----------|--------|
| Indices | ES, NQ, YM, RTY | 09:30–16:15 | NYSE open + 15min futures close |
| Energy | CL, NG, RB, HO | 09:00–14:30 | NYMEX pit |
| Precious metals | GC, SI | 08:20–13:30 | COMEX pit |
| Base metals | HG, PL | 08:20–13:30 | COMEX/NYMEX pit |
| Currencies | 6E, 6B, 6J, 6A, 6C, 6S | 08:20–16:00 | IMM pit + electronic extension |
| Treasuries | ZN, ZF, ZT, US | 08:20–15:00 | CBOT pit |
| Crypto | BTC | 09:30–16:00 | CME-defined, follows equity hours |

### CBOT Grains (exception)

Different maintenance window: 14:20–20:00 ET (340 min).
ETH: 20:00–14:20 ET.

| Group | Products | RTH (ET) | Origin |
|-------|----------|----------|--------|
| Grains | ZC, ZW, ZS | 09:30–14:20 | CBOT pit, confirmed CME docs |

## EUREX

Maintenance 16:00–19:15 ET. ETH: 19:15–16:00 ET.

| Group | Products | RTH (ET) | Origin |
|-------|----------|----------|--------|
| European indices | FDAX, FESX | 03:00–11:30 | Xetra hours (09:00–17:30 CET) |

## ICE

### ICE Europe (BRN)

Maintenance ~17:00–20:00 ET. ETH: 20:00–17:00 ET.

| Group | Products | RTH (ET) | Origin |
|-------|----------|----------|--------|
| Brent | BRN | 03:00–14:30 | London hours, volume-based |

### ICE US (KC, CC)

Short sessions, no overnight. ETH = RTH.

| Product | ETH/RTH (ET) |
|---------|-------------|
| KC (Coffee) | 04:15–13:25 |
| CC (Cocoa) | 04:45–13:25 |

## Notes

- RTH is always a subset of ETH (except KC, CC where ETH = RTH)
- Currency RTH extends to 16:00 (beyond old pit close at 15:00) because electronic volume stays high
- All CME times published in CT (Central Time). ET = CT + 1 hour
- EUREX CET = ET + 6 hours (standard time)
