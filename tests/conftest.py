"""Test fixtures. Real NQ data, fixed slice for deterministic tests."""

import pytest

from barb.data import load_data
from config.market.instruments import get_instrument


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
    """NQ session config — from instrument config, not hardcoded."""
    return get_instrument("NQ")["sessions"]
