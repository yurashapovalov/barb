"""Shared fixtures for function tests."""

import pandas as pd
import pytest


@pytest.fixture
def df():
    """DataFrame with DatetimeIndex for function tests."""
    dates = pd.date_range("2024-01-02", periods=10, freq="D")  # Tue Jan 2
    return pd.DataFrame({
        "open": [100, 102, 101, 105, 103, 99, 104, 106, 102, 100],
        "high": [105, 106, 104, 108, 107, 103, 108, 110, 106, 104],
        "low": [98, 100, 99, 103, 101, 97, 102, 104, 100, 98],
        "close": [103, 101, 103, 106, 104, 100, 107, 105, 101, 102],
        "volume": [1000, 1500, 1200, 2000, 800, 1100, 1800, 900, 1400, 1300],
    }, index=dates, dtype=float)
