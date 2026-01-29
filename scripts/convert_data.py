#!/usr/bin/env python3
"""Convert raw market data from TXT to Parquet format with enriched columns."""

from pathlib import Path

import polars as pl


def convert_txt_to_parquet(input_path: Path, output_path: Path, instrument: str) -> None:
    """Convert a TXT file to Parquet with additional computed columns."""

    print(f"Reading {input_path}...")

    # Read CSV without headers
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

    print(f"Loaded {len(df):,} rows")

    # Parse timestamp, add instrument, keep only raw data
    df = df.with_columns([
        pl.col("timestamp").str.to_datetime("%Y-%m-%d %H:%M:%S").alias("timestamp"),
        pl.lit(instrument).alias("instrument"),
    ])

    # Only raw OHLCV data - everything else computed on the fly
    df = df.select([
        "instrument",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ])

    print(f"Writing to {output_path}...")
    df.write_parquet(output_path, compression="zstd")

    # Print stats
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Done! Output size: {file_size_mb:.1f} MB")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # Sample output
    print("\nSample data:")
    print(df.head(5))


def main():
    data_dir = Path(__file__).parent.parent / "data"

    # Convert NQ
    nq_input = data_dir / "NQ.txt"
    nq_output = data_dir / "NQ.parquet"

    if nq_input.exists():
        convert_txt_to_parquet(nq_input, nq_output, "NQ")
    else:
        print(f"File not found: {nq_input}")


if __name__ == "__main__":
    main()
