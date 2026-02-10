#!/usr/bin/env python3
"""Convert raw TXT market data to Parquet.

Converts all .txt files in data/1d/ and data/1m/ to .parquet (zstd).

Formats:
  1d: date,open,high,low,close,volume,oi  (7 cols, date only)
  1m: datetime,open,high,low,close,volume  (6 cols)

Usage:
  python scripts/convert_data.py          # convert all
  python scripts/convert_data.py --clean  # convert all + delete txt after
"""

import argparse
from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).parent.parent / "data"


def convert_daily(input_path: Path, output_path: Path) -> int:
    """Convert daily TXT (date,O,H,L,C,vol,OI) to parquet."""
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
    """Convert minute TXT (datetime,O,H,L,C,vol) to parquet."""
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


def convert_dir(data_dir: Path, timeframe: str, clean: bool) -> None:
    """Convert all txt files in a directory."""
    src_dir = data_dir / timeframe
    if not src_dir.exists():
        print(f"  {src_dir} not found, skipping")
        return

    txt_files = sorted(src_dir.glob("*.txt"))
    if not txt_files:
        print(f"  No .txt files in {src_dir}")
        return

    converter = convert_daily if timeframe == "1d" else convert_minute

    for txt_path in txt_files:
        symbol = txt_path.stem
        parquet_path = txt_path.with_suffix(".parquet")

        rows = converter(txt_path, parquet_path)
        size_mb = parquet_path.stat().st_size / (1024 * 1024)
        print(f"  {symbol}: {rows:,} rows → {size_mb:.1f} MB")

        if clean:
            txt_path.unlink()


def main():
    parser = argparse.ArgumentParser(description="Convert TXT market data to Parquet")
    parser.add_argument("--clean", action="store_true", help="Delete txt files after conversion")
    args = parser.parse_args()

    print("Converting 1d (daily)...")
    convert_dir(DATA_DIR, "1d", args.clean)

    print("\nConverting 1m (minute)...")
    convert_dir(DATA_DIR, "1m", args.clean)

    # Remove old monolithic parquet if exists
    old_parquet = DATA_DIR / "NQ.parquet"
    if old_parquet.exists():
        old_parquet.unlink()
        print(f"\nDeleted old {old_parquet}")

    print("\nDone.")


if __name__ == "__main__":
    main()
