#!/usr/bin/env python3
"""Daily data update from FirstRateData API.

Downloads latest bars and appends to existing parquet files.
Designed to run as a cron job.

Usage:
  python scripts/update_data.py --type futures
  python scripts/update_data.py --type futures --period full  # re-download everything
"""

import argparse
import io
import logging
import os
import sys
import zipfile
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv

DATA_DIR = Path(__file__).parent.parent / "data"
load_dotenv(DATA_DIR.parent / ".env")

API_BASE = "https://firstratedata.com/api"
API_USERID = "XMbX1O2zD0--j0RfUK-W9A"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

log = logging.getLogger("update_data")

# Provider ticker → our symbol
SYMBOL_MAP = {
    "A6": "6A",
    "AD": "6C",
    "B": "BRN",
    "B6": "6B",
    "E1": "6S",
    "E6": "6E",
    "J1": "6J",
}

# Tickers we care about, per asset type (provider names)
TARGET_TICKERS = {
    "futures": {
        "ES",
        "NQ",
        "YM",
        "RTY",
        "FDAX",
        "FESX",
        "CL",
        "B",
        "NG",
        "RB",
        "HO",
        "GC",
        "SI",
        "HG",
        "PL",
        "E6",
        "B6",
        "J1",
        "A6",
        "AD",
        "E1",
        "ZN",
        "ZF",
        "ZT",
        "US",
        "ZC",
        "ZW",
        "ZS",
        "KC",
        "CC",
        "BTC",
    },
}

# API timeframe → our directory
TIMEFRAMES = {
    "1day": "1d",
    "1min": "1m",
}

DAILY_COLS = ["timestamp", "open", "high", "low", "close", "volume", "oi"]
MINUTE_COLS = ["timestamp", "open", "high", "low", "close", "volume"]
KEEP_COLS = ["timestamp", "open", "high", "low", "close", "volume"]


def extract_ticker(filename: str) -> str | None:
    """Extract provider ticker from filename like 'NQ_day_1day_continuous_UNadjusted.txt'."""
    parts = filename.split("_")
    if len(parts) >= 2:
        return parts[0]
    return None


def parse_daily_txt(data: bytes) -> pd.DataFrame:
    """Parse daily txt: date,O,H,L,C,volume,OI → DataFrame."""
    df = pd.read_csv(io.BytesIO(data), header=None, names=DAILY_COLS)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df[KEEP_COLS]


def parse_minute_txt(data: bytes) -> pd.DataFrame:
    """Parse minute txt: datetime,O,H,L,C,volume → DataFrame."""
    df = pd.read_csv(io.BytesIO(data), header=None, names=MINUTE_COLS)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def update_supabase_data_end(client: httpx.Client, asset_type: str, date: str) -> None:
    """Update data_end for all instruments of this asset type in Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.warning("SUPABASE_URL/SUPABASE_SERVICE_KEY not set, skipping data_end update")
        return

    resp = client.patch(
        f"{SUPABASE_URL}/rest/v1/instruments?type=eq.{asset_type}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json={"data_end": date},
    )
    resp.raise_for_status()
    log.info("Supabase: data_end → %s for type=%s", date, asset_type)


def check_last_update(client: httpx.Client, asset_type: str) -> str:
    """Get last update date from API. Returns date string like '2026-02-10'."""
    resp = client.get(
        f"{API_BASE}/last_update",
        params={"type": asset_type, "userid": API_USERID},
    )
    resp.raise_for_status()
    return resp.text.strip()


def read_state(state_path: Path) -> str | None:
    """Read last processed date from state file."""
    if state_path.exists():
        return state_path.read_text().strip()
    return None


def write_state(state_path: Path, date: str) -> None:
    state_path.write_text(date)


def download_zip(client: httpx.Client, asset_type: str, period: str, timeframe: str) -> bytes:
    """Download data zip from API. Follows redirects (Backblaze B2)."""
    log.info("Downloading %s %s %s...", asset_type, period, timeframe)
    resp = client.get(
        f"{API_BASE}/data_file",
        params={
            "type": asset_type,
            "period": period,
            "timeframe": timeframe,
            "adjustment": "contin_UNadj",
            "userid": API_USERID,
        },
    )
    resp.raise_for_status()
    log.info("Downloaded %.1f MB", len(resp.content) / (1024 * 1024))
    return resp.content


def append_bars(existing_path: Path, new_df: pd.DataFrame) -> int:
    """Append new bars to existing parquet, deduplicate by timestamp.

    Atomic write: writes to .tmp then renames. If crash mid-write,
    original file stays intact.

    Returns total row count after append.
    """
    if existing_path.exists():
        existing = pd.read_parquet(existing_path)
        combined = (
            pd.concat([existing, new_df])
            .drop_duplicates(subset=["timestamp"], keep="last")
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
    else:
        combined = new_df.sort_values("timestamp").reset_index(drop=True)

    tmp_path = existing_path.with_suffix(".parquet.tmp")
    combined.to_parquet(tmp_path, compression="zstd", index=False)
    tmp_path.rename(existing_path)
    return len(combined)


def process_zip(
    zip_data: bytes,
    api_timeframe: str,
    asset_type: str,
    target_tickers: set[str],
) -> dict[str, int]:
    """Extract zip, parse txt files, append to parquets.

    Returns dict of {symbol: new_rows} for processed tickers.
    """
    our_tf = TIMEFRAMES[api_timeframe]
    out_dir = DATA_DIR / our_tf / asset_type
    out_dir.mkdir(parents=True, exist_ok=True)

    parser = parse_daily_txt if api_timeframe == "1day" else parse_minute_txt
    results = {}

    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        for name in zf.namelist():
            if not name.endswith(".txt"):
                continue

            ticker = extract_ticker(Path(name).name)
            if not ticker or ticker not in target_tickers:
                continue

            symbol = SYMBOL_MAP.get(ticker, ticker)
            data = zf.read(name)

            if not data.strip():
                continue

            new_df = parser(data)
            if len(new_df) == 0:
                continue

            parquet_path = out_dir / f"{symbol}.parquet"
            total = append_bars(parquet_path, new_df)
            new_rows = len(new_df)
            results[symbol] = new_rows
            log.info("  %s: +%d rows (total: %d)", symbol, new_rows, total)

    return results


def main():
    parser = argparse.ArgumentParser(description="Update market data from FirstRateData")
    parser.add_argument("--type", required=True, help="Asset type (futures, stocks, crypto, etc.)")
    parser.add_argument(
        "--period",
        default="day",
        choices=["day", "week", "month", "full"],
        help="Data period to download (default: day)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip last_update check, download regardless",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check for updates but don't download",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    asset_type = args.type
    target_tickers = TARGET_TICKERS.get(asset_type)
    if not target_tickers:
        log.error("No target tickers configured for type=%s", asset_type)
        sys.exit(1)

    state_path = DATA_DIR / asset_type / ".last_update"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(follow_redirects=True, timeout=300) as client:
        # Check if new data available
        remote_date = check_last_update(client, asset_type)
        local_date = read_state(state_path)
        log.info("Remote: %s, Local: %s", remote_date, local_date)

        if not args.force and local_date == remote_date:
            log.info("Already up to date. Use --force to re-download.")
            return

        if args.dry_run:
            log.info("New data available: %s (dry run, skipping download)", remote_date)
            return

        # Download and process both timeframes
        total_updated = 0
        for api_tf in TIMEFRAMES:
            zip_data = download_zip(client, asset_type, args.period, api_tf)
            results = process_zip(zip_data, api_tf, asset_type, target_tickers)
            total_updated += len(results)
            log.info("%s %s: updated %d tickers", asset_type, api_tf, len(results))

        # Update Supabase metadata
        update_supabase_data_end(client, asset_type, remote_date)

        # Save state
        write_state(state_path, remote_date)
        log.info("Done. Updated %d ticker-timeframe pairs. State: %s", total_updated, remote_date)


if __name__ == "__main__":
    main()
