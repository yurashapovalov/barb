"""Data loading."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"


@lru_cache
def load_data(instrument: str, timeframe: str = "1d", asset_type: str = "futures") -> pd.DataFrame:
    """Load instrument data as pandas DataFrame with DatetimeIndex.

    Args:
        instrument: Symbol name (e.g. "NQ", "ES")
        timeframe: "1d" for daily bars, "1m" for minute bars
        asset_type: Asset class subdirectory (e.g. "futures", "stocks")
    """
    path = DATA_DIR / timeframe / asset_type / f"{instrument.upper()}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    df = pd.read_parquet(path)
    if "timestamp" in df.columns:
        df = df.set_index("timestamp")
    df = df[["open", "high", "low", "close", "volume"]]
    return df.sort_index()
