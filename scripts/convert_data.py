#!/usr/bin/env python3
"""Convert raw TXT market data to Parquet.

Reads from a source directory (provider archive), converts selected tickers
to data/1d/ and data/1m/ with symbol mapping applied.

Formats:
  1d: date,open,high,low,close,volume,oi  (7 cols, date only)
  1m: datetime,open,high,low,close,volume  (6 cols)

Usage:
  python scripts/convert_data.py data/futures_full_1day_contin_UNadj_wzfwlhb
  python scripts/convert_data.py data/futures_full_1min_contin_UNadj_xyz --timeframe 1m
"""

import argparse
from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).parent.parent / "data"

# Provider ticker → our symbol (TradingView names)
SYMBOL_MAP = {
    "A6": "6A",
    "AD": "6C",
    "B": "BRN",
    "B6": "6B",
    "E1": "6S",
    "E6": "6E",
    "J1": "6J",
}

# 31 target tickers (provider names)
TARGET_TICKERS = {
    # Indices
    "ES",
    "NQ",
    "YM",
    "RTY",
    "FDAX",
    "FESX",
    # Energy
    "CL",
    "B",
    "NG",
    "RB",
    "HO",
    # Metals
    "GC",
    "SI",
    "HG",
    "PL",
    # Currencies
    "E6",
    "B6",
    "J1",
    "A6",
    "AD",
    "E1",
    # Treasuries
    "ZN",
    "ZF",
    "ZT",
    "US",
    # Agriculture
    "ZC",
    "ZW",
    "ZS",
    "KC",
    "CC",
    # Crypto
    "BTC",
}


def convert_daily(input_path: Path, output_path: Path) -> int:
    df = pl.read_csv(
        input_path,
        has_header=False,
        new_columns=["timestamp", "open", "high", "low", "close", "volume", "oi"],
        schema={
            "timestamp": pl.Utf8,
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume": pl.Int64,
            "oi": pl.Int64,
        },
    )
    df = df.with_columns(
        pl.col("timestamp").str.to_datetime("%Y-%m-%d").alias("timestamp"),
    ).select(["timestamp", "open", "high", "low", "close", "volume"])

    df.write_parquet(output_path, compression="zstd")
    return len(df)


def convert_minute(input_path: Path, output_path: Path) -> int:
    df = pl.read_csv(
        input_path,
        has_header=False,
        new_columns=["timestamp", "open", "high", "low", "close", "volume"],
        schema={
            "timestamp": pl.Utf8,
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume": pl.Int64,
        },
    )
    df = df.with_columns(
        pl.col("timestamp").str.to_datetime("%Y-%m-%d %H:%M:%S").alias("timestamp"),
    )

    df.write_parquet(output_path, compression="zstd")
    return len(df)


def extract_ticker(filename: str) -> str | None:
    """Extract provider ticker from filename like 'NQ_full_1day_continuous_UNadjusted.txt'."""
    parts = filename.split("_")
    if len(parts) >= 2:
        return parts[0]
    return None


def main():
    parser = argparse.ArgumentParser(description="Convert TXT market data to Parquet")
    parser.add_argument("source_dir", help="Directory with provider txt files")
    parser.add_argument(
        "--timeframe",
        default="1d",
        choices=["1d", "1m"],
        help="Target timeframe directory (default: 1d)",
    )
    parser.add_argument(
        "--type",
        default="futures",
        help="Asset type subdirectory (default: futures)",
    )
    args = parser.parse_args()

    src_dir = Path(args.source_dir)
    if not src_dir.exists():
        print(f"Source directory not found: {src_dir}")
        return

    out_dir = DATA_DIR / args.timeframe / args.type
    out_dir.mkdir(parents=True, exist_ok=True)

    converter = convert_daily if args.timeframe == "1d" else convert_minute

    txt_files = sorted(src_dir.glob("*.txt"))
    converted = 0
    skipped = 0

    for txt_path in txt_files:
        provider_ticker = extract_ticker(txt_path.name)
        if not provider_ticker or provider_ticker not in TARGET_TICKERS:
            skipped += 1
            continue

        our_symbol = SYMBOL_MAP.get(provider_ticker, provider_ticker)
        out_path = out_dir / f"{our_symbol}.parquet"

        rows = converter(txt_path, out_path)
        size_kb = out_path.stat().st_size / 1024
        print(f"  {provider_ticker:>4} → {our_symbol:<4}  {rows:>5,} rows  {size_kb:.0f} KB")
        converted += 1

    print(f"\nConverted: {converted}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
