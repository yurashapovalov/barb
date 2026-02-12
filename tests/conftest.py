"""Test fixtures. Real NQ data, fixed slice for deterministic tests."""

import pytest

from barb.data import load_data
from config.market.instruments import get_instrument, register_instrument

# NQ config matching Supabase instrument_full format
_NQ_ROW = {
    "symbol": "NQ",
    "name": "Nasdaq 100 E-mini",
    "exchange": "CME",
    "type": "futures",
    "category": "index",
    "currency": "USD",
    "default_session": "RTH",
    "data_start": "2008-01-02",
    "data_end": "2026-02-11",
    "events": ["macro", "options"],
    "notes": None,
    "config": {
        "sessions": {
            "ETH": ["18:00", "17:00"],
            "RTH": ["09:30", "16:15"],
        },
        "tick_size": 0.25,
        "tick_value": 5.0,
        "point_value": 20.0,
    },
    "exchange_timezone": "CT",
    "exchange_name": "Chicago Mercantile Exchange",
}


@pytest.fixture(scope="session", autouse=True)
def _register_instruments():
    """Register test instruments before the test session."""
    register_instrument(_NQ_ROW)


@pytest.fixture(scope="session")
def nq_daily():
    """Full daily NQ data (settlement close, matches TradingView)."""
    return load_data("NQ", "1d")


@pytest.fixture(scope="session")
def nq_minute():
    """Full minute-level NQ data as pandas DataFrame with DatetimeIndex."""
    return load_data("NQ", "1m")


@pytest.fixture(scope="session")
def nq_minute_slice(nq_minute):
    """Fixed 6-month slice of minute data. All numeric tests use this."""
    return nq_minute["2024-01-01":"2024-06-30"]


@pytest.fixture(scope="session")
def sessions():
    """NQ session config — from instrument config, not hardcoded."""
    return get_instrument("NQ")["sessions"]
