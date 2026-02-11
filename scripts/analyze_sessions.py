#!/usr/bin/env python3
"""Analyze trading sessions from minute data.

Scans minute bars to determine:
- Maintenance window (gap with no data)
- ETH boundaries (first/last bar around the gap)
- RTH estimate (where volume is concentrated)

All times in US/Eastern (same as our data).

Usage:
  python scripts/analyze_sessions.py
  python scripts/analyze_sessions.py GC NQ ES
"""

import sys
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data" / "1m"


def analyze_instrument(symbol: str) -> dict:
    path = DATA_DIR / f"{symbol}.parquet"
    if not path.exists():
        return {"error": f"No data: {path}"}

    df = pd.read_parquet(path)
    if "timestamp" in df.columns:
        df = df.set_index("timestamp")
    # Use last 2 months for stable results
    recent = df.loc["2025-12":"2026-02"]
    if len(recent) == 0:
        recent = df.tail(50000)

    recent = recent.copy()
    recent["minute"] = recent.index.hour * 60 + recent.index.minute

    # Count bars per minute-of-day (0-1439)
    bar_count = recent.groupby("minute")["close"].count()

    # Find maintenance gap: consecutive minutes with 0 bars
    all_minutes = set(range(1440))
    active_minutes = set(bar_count[bar_count > 0].index)
    inactive_minutes = sorted(all_minutes - active_minutes)

    # Find the longest gap
    gap_start = None
    gap_end = None
    longest = 0
    if inactive_minutes:
        runs = []
        run_start = inactive_minutes[0]
        prev = inactive_minutes[0]
        for m in inactive_minutes[1:]:
            if m == prev + 1:
                prev = m
            else:
                runs.append((run_start, prev))
                run_start = m
                prev = m
        runs.append((run_start, prev))

        # Longest run = maintenance window
        best = max(runs, key=lambda r: r[1] - r[0])
        gap_start = best[0]
        gap_end = best[1]
        longest = gap_end - gap_start + 1

    # ETH: from end of gap to start of gap
    eth_start = (gap_end + 1) % 1440 if gap_end is not None else 0
    eth_end = (gap_start - 1) % 1440 if gap_start is not None else 1439

    # Volume by hour
    recent["hour"] = recent.index.hour
    hourly_vol = recent.groupby("hour")["volume"].sum()

    # RTH estimate: hours where volume > 50% of peak hour
    if len(hourly_vol) > 0:
        peak_vol = hourly_vol.max()
        threshold = peak_vol * 0.4
        rth_hours = sorted(hourly_vol[hourly_vol >= threshold].index.tolist())
    else:
        rth_hours = []

    def fmt_time(minutes):
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def fmt_hour(h):
        return f"{h:02d}:00"

    return {
        "symbol": symbol,
        "maintenance": f"{fmt_time(gap_start)}–{fmt_time(gap_end)}"
        if gap_start is not None
        else "none",
        "maintenance_minutes": longest,
        "eth": f"{fmt_time(eth_start)}–{fmt_time(eth_end)}",
        "rth_hours": f"{fmt_hour(rth_hours[0])}–{fmt_hour(rth_hours[-1] + 1)}"
        if rth_hours
        else "unknown",
        "rth_range": rth_hours,
        "peak_hour": int(hourly_vol.idxmax()) if len(hourly_vol) > 0 else None,
        "hourly_vol": hourly_vol,
    }


def print_volume_profile(result: dict):
    hourly = result.get("hourly_vol")
    if hourly is None or len(hourly) == 0:
        return
    max_vol = hourly.max()
    rth = set(result.get("rth_range", []))
    for h in range(24):
        vol = hourly.get(h, 0)
        bar = "█" * int(vol / max_vol * 30) if max_vol > 0 else ""
        marker = " ◄ RTH" if h in rth else ""
        print(f"    {h:02d}:00  {vol:>12,}  {bar}{marker}")


def main():
    symbols = sys.argv[1:] if len(sys.argv) > 1 else None

    if symbols is None:
        # All instruments
        files = sorted(DATA_DIR.glob("*.parquet"))
        symbols = [f.stem for f in files]

    for symbol in symbols:
        result = analyze_instrument(symbol)

        if "error" in result:
            print(f"\n{symbol}: {result['error']}")
            continue

        print(f"\n{'=' * 60}")
        print(f"  {result['symbol']}")
        print(f"  Maintenance: {result['maintenance']} ({result['maintenance_minutes']} min)")
        print(f"  ETH: {result['eth']}")
        print(f"  RTH (estimated): {result['rth_hours']}")
        print(f"  Peak hour: {result['peak_hour']:02d}:00")
        print()
        print_volume_profile(result)


if __name__ == "__main__":
    main()
