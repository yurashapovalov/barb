"""Data loading."""

from functools import lru_cache
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).parent.parent / "data"


@lru_cache
def load_data(instrument: str) -> pd.DataFrame:
    """Load instrument minute data as pandas DataFrame with DatetimeIndex."""
    path = DATA_DIR / f"{instrument.upper()}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    df = pd.read_parquet(path)
    if "timestamp" in df.columns:
        df = df.set_index("timestamp")
    df = df[["open", "high", "low", "close", "volume"]]
    return df.sort_index()
