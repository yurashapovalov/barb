"""Test fixtures. Real NQ data, fixed slice for deterministic tests."""

import pytest

from barb.data import load_data


@pytest.fixture(scope="session")
def nq_minute():
    """Full minute-level NQ data as pandas DataFrame with DatetimeIndex."""
    return load_data("NQ")


@pytest.fixture(scope="session")
def nq_minute_slice(nq_minute):
    """Fixed 6-month slice of minute data. All numeric tests use this."""
    return nq_minute["2024-01-01":"2024-06-30"]


@pytest.fixture
def sessions():
    """NQ session config."""
    return {
        "ETH": ("18:00", "17:00"),
        "OVERNIGHT": ("18:00", "09:30"),
        "ASIAN": ("18:00", "03:00"),
        "EUROPEAN": ("03:00", "09:30"),
        "RTH": ("09:30", "17:00"),
        "RTH_OPEN": ("09:30", "10:30"),
        "MORNING": ("09:30", "12:30"),
        "AFTERNOON": ("12:30", "17:00"),
        "RTH_CLOSE": ("16:00", "17:00"),
    }
