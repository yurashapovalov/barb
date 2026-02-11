#!/usr/bin/env python3
"""Compare provider 1d bars vs 1m ETH-aggregated bars.

Proves whether building daily from minute data with correct ETH window
matches TradingView (last trade close) vs provider settlement close.

Usage:
    .venv/bin/python scripts/compare_daily.py
    .venv/bin/python scripts/compare_daily.py 2026-01-15
"""

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

# ETH windows per instrument (from sessions-reference.md, all in ET)
ETH_WINDOWS = {
    # CME/COMEX/NYMEX: 18:00-17:00
    "NQ": ("18:00", "17:00"),
    "ES": ("18:00", "17:00"),
    "YM": ("18:00", "17:00"),
    "RTY": ("18:00", "17:00"),
    "CL": ("18:00", "17:00"),
    "NG": ("18:00", "17:00"),
    "RB": ("18:00", "17:00"),
    "HO": ("18:00", "17:00"),
    "GC": ("18:00", "17:00"),
    "SI": ("18:00", "17:00"),
    "HG": ("18:00", "17:00"),
    "PL": ("18:00", "17:00"),
    "6A": ("18:00", "17:00"),
    "6B": ("18:00", "17:00"),
    "6C": ("18:00", "17:00"),
    "6E": ("18:00", "17:00"),
    "6J": ("18:00", "17:00"),
    "6S": ("18:00", "17:00"),
    "ZN": ("18:00", "17:00"),
    "ZF": ("18:00", "17:00"),
    "ZT": ("18:00", "17:00"),
    "US": ("18:00", "17:00"),
    "BTC": ("18:00", "17:00"),
    # CBOT Grains: 20:00-14:20
    "ZC": ("20:00", "14:20"),
    "ZW": ("20:00", "14:20"),
    "ZS": ("20:00", "14:20"),
    # EUREX: 19:15-16:00
    "FDAX": ("19:15", "16:00"),
    "FESX": ("19:15", "16:00"),
    # ICEEUR: 20:00-17:00
    "BRN": ("20:00", "17:00"),
    # ICEUS: same-day sessions
    "CC": ("04:45", "13:25"),
    "KC": ("04:15", "13:25"),
}


def aggregate_eth(symbol, date_str, eth):
    path = DATA_DIR / "1m" / f"{symbol}.parquet"
    if not path.exists():
        return None
    m = pd.read_parquet(path)
    if "timestamp" in m.columns:
        m = m.set_index("timestamp")

    date = pd.Timestamp(date_str)
    start_h, start_m = int(eth[0].split(":")[0]), int(eth[0].split(":")[1])
    end_h, end_m = int(eth[1].split(":")[0]), int(eth[1].split(":")[1])

    if start_h > end_h or (start_h == end_h and start_m > end_m):
        prev_day = date - pd.Timedelta(days=1)
        t_start = prev_day.replace(hour=start_h, minute=start_m)
        t_end = date.replace(hour=end_h, minute=end_m) - pd.Timedelta(minutes=1)
    else:
        t_start = date.replace(hour=start_h, minute=start_m)
        t_end = date.replace(hour=end_h, minute=end_m) - pd.Timedelta(minutes=1)

    day = m.loc[t_start:t_end]
    if len(day) == 0:
        return None

    return {
        "O": day.iloc[0]["open"],
        "H": day["high"].max(),
        "L": day["low"].min(),
        "C": day.iloc[-1]["close"],
        "bars": len(day),
        "last_bar": str(day.index[-1]),
    }


def get_1d(symbol, date_str):
    path = DATA_DIR / "1d" / f"{symbol}.parquet"
    if not path.exists():
        return None
    d = pd.read_parquet(path)
    row = d[d["timestamp"] == date_str]
    if len(row) == 0:
        return None
    r = row.iloc[0]
    return {"O": r["open"], "H": r["high"], "L": r["low"], "C": r["close"]}


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else "2025-12-22"

    print(f"=== OHLC Comparison: {date} ===")
    print("1d = provider daily bars (settlement close)")
    print("1m→ETH = aggregated from minute bars with ETH window (last trade close)")
    print()

    rows = []
    for sym in sorted(ETH_WINDOWS.keys()):
        d1 = get_1d(sym, date)
        agg = aggregate_eth(sym, date, ETH_WINDOWS[sym])

        if not d1 and not agg:
            continue

        if d1 and agg:
            o_ok = d1["O"] == agg["O"]
            h_ok = d1["H"] == agg["H"]
            l_ok = d1["L"] == agg["L"]
            c_diff = agg["C"] - d1["C"]
            c_pct = (c_diff / d1["C"] * 100) if d1["C"] != 0 else 0

            o_m = "✅" if o_ok else "❌"
            h_m = "✅" if h_ok else "❌"
            l_m = "✅" if l_ok else "❌"

            rows.append(
                {
                    "sym": sym,
                    "o_m": o_m,
                    "h_m": h_m,
                    "l_m": l_m,
                    "c_diff": c_diff,
                    "c_pct": c_pct,
                    "d1": d1,
                    "agg": agg,
                }
            )

            print(
                f"{sym:>5}  1d:    O={d1['O']:>12}  H={d1['H']:>12}  L={d1['L']:>12}  C={d1['C']:>12}"
            )
            print(
                f"       1m→ETH O={agg['O']:>12}  H={agg['H']:>12}  L={agg['L']:>12}  C={agg['C']:>12}  ({agg['bars']} bars)"
            )
            print(
                f"       OHL: {o_m}{h_m}{l_m}  Δclose: {c_diff:+.6f} ({c_pct:+.4f}%)  last_bar: {agg['last_bar']}"
            )
        elif agg:
            rows.append(
                {
                    "sym": sym,
                    "o_m": "—",
                    "h_m": "—",
                    "l_m": "—",
                    "c_diff": 0,
                    "c_pct": 0,
                    "d1": None,
                    "agg": agg,
                }
            )
            print(
                f"{sym:>5}  1m→ETH O={agg['O']:>12}  H={agg['H']:>12}  L={agg['L']:>12}  C={agg['C']:>12}  ({agg['bars']} bars) [NO 1d]"
            )
        elif d1:
            print(
                f"{sym:>5}  1d:    O={d1['O']:>12}  H={d1['H']:>12}  L={d1['L']:>12}  C={d1['C']:>12}  [NO 1m]"
            )
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY — for TV verification")
    print(f"Date: {date}")
    print()
    print(f"{'Symbol':>6} | {'O':>12} | {'H':>12} | {'L':>12} | {'C':>12} | {'Δclose':>10} | OHL")
    print("-" * 85)
    for r in rows:
        agg = r["agg"]
        print(
            f"{r['sym']:>6} | {agg['O']:>12} | {agg['H']:>12} | {agg['L']:>12} | {agg['C']:>12} | {r['c_diff']:>+10.4f} | {r['o_m']}{r['h_m']}{r['l_m']}"
        )


if __name__ == "__main__":
    main()
