# Session Analysis from Minute Data

All times in US/Eastern. Derived from volume profiles of minute bars (2025-12 to 2026-02).

## Exchange Patterns

### CME/COMEX/NYMEX (maintenance 17:00–18:00, 60 min)
ETH: 18:00–17:00

### CBOT Grains (maintenance 14:20–20:00, 340 min)
ETH: 20:00–14:20

### ICE US (CC, KC — no overnight)
ETH: 04:00–13:30 (only trades during these hours)

### ICE EUR (BRN — near 24h)
Trades almost continuously, small gap around 17:00–20:00

## Instruments

### Indices
| Symbol | Exchange | Maintenance | ETH | RTH (volume) | Peak |
|--------|----------|-------------|-----|---------------|------|
| NQ | CME | 17:00–18:00 | 18:00–17:00 | 09:30–16:15 | 10:00 |
| ES | CME | 17:00–18:00 | 18:00–17:00 | 09:30–16:15 | 10:00 |
| YM | CBOT | 17:00–18:00 | 18:00–17:00 | 09:30–16:15 | 09:00 |
| RTY | CME | 17:00–18:00 | 18:00–17:00 | 09:30–16:15 | 09:00 |
| FDAX | EUREX | 16:00–19:15 | 19:15–16:00 | 03:00–11:30 | 03:00 |
| FESX | EUREX | 16:00–19:15 | 19:15–16:00 | 03:00–11:30 | 11:00 |

### Energy
| Symbol | Exchange | Maintenance | ETH | RTH (volume) | Peak |
|--------|----------|-------------|-----|---------------|------|
| CL | NYMEX | 17:00–18:00 | 18:00–17:00 | 09:00–14:30 | 09:00 |
| BRN | ICEEUR | ~17:00–20:00 | 20:00–17:00 | 03:00–14:30 | 11:00 |
| NG | NYMEX | 17:00–18:00 | 18:00–17:00 | 09:00–14:30 | 09:00 |
| RB | NYMEX | 17:00–18:00 | 18:00–17:00 | 09:00–14:30 | 14:00 |
| HO | NYMEX | 17:00–18:00 | 18:00–17:00 | 09:00–14:30 | 09:00 |

### Metals
| Symbol | Exchange | Maintenance | ETH | RTH (volume) | Peak |
|--------|----------|-------------|-----|---------------|------|
| GC | COMEX | 17:00–18:00 | 18:00–17:00 | 08:20–13:30 | 10:00 |
| SI | COMEX | 17:00–18:00 | 18:00–17:00 | 08:20–13:30 | 10:00 |
| HG | COMEX | 17:00–18:00 | 18:00–17:00 | 08:20–13:30 | 09:00 |
| PL | NYMEX | 17:00–18:00 | 18:00–17:00 | 08:20–13:30 | 09:00 |

### Currencies
| Symbol | Exchange | Maintenance | ETH | RTH (volume) | Peak |
|--------|----------|-------------|-----|---------------|------|
| 6E | CME | 17:00–18:00 | 18:00–17:00 | 08:20–16:00 | 10:00 |
| 6B | CME | 17:00–18:00 | 18:00–17:00 | 08:20–16:00 | 10:00 |
| 6J | CME | 17:00–18:00 | 18:00–17:00 | 08:20–16:00 | 10:00 |
| 6A | CME | 17:00–18:00 | 18:00–17:00 | 08:20–16:00 | 10:00 |
| 6C | CME | 17:00–18:00 | 18:00–17:00 | 08:20–16:00 | 10:00 |
| 6S | CME | 17:00–18:00 | 18:00–17:00 | 08:20–16:00 | 10:00 |

### Treasuries
| Symbol | Exchange | Maintenance | ETH | RTH (volume) | Peak |
|--------|----------|-------------|-----|---------------|------|
| ZN | CBOT | 17:00–18:00 | 18:00–17:00 | 08:20–15:00 | 10:00 |
| ZF | CBOT | 17:00–18:00 | 18:00–17:00 | 08:20–15:00 | 10:00 |
| ZT | CBOT | 17:00–18:00 | 18:00–17:00 | 08:20–15:00 | 08:00 |
| US | CBOT | 17:00–18:00 | 18:00–17:00 | 08:20–15:00 | 10:00 |

### Agriculture
| Symbol | Exchange | Maintenance | ETH | RTH (volume) | Peak |
|--------|----------|-------------|-----|---------------|------|
| ZC | CBOT | 14:20–20:00 | 20:00–14:20 | 09:30–14:15 | 09:00 |
| ZW | CBOT | 14:20–20:00 | 20:00–14:20 | 09:30–14:15 | 09:00 |
| ZS | CBOT | 14:20–20:00 | 20:00–14:20 | 09:30–14:15 | 10:00 |
| KC | ICEUS | 13:30–04:00 | 04:15–13:25 | 04:15–13:25 | 10:00 |
| CC | ICEUS | 13:30–04:00 | 04:45–13:25 | 04:45–13:25 | 11:00 |

### Crypto
| Symbol | Exchange | Maintenance | ETH | RTH (volume) | Peak |
|--------|----------|-------------|-----|---------------|------|
| BTC | CME | 17:00–18:00 | 18:00–17:00 | 09:30–16:00 | 10:00 |

## Notes

- RTH times are approximate, based on where volume concentrates (>40% of peak hour)
- Some instruments (6J, GC, SI, HG, PL) have secondary volume peak at 20:00 ET (Asia open)
- CBOT grains have much longer maintenance window (5h 40min vs 1h for CME)
- ICE soft commodities (CC, KC) only trade ~9 hours/day
- BRN (Brent) has unique near-24h profile with European peak
