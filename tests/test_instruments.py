"""Tests for config/market/instruments.py — instrument registry."""

import pytest

from config.market.instruments import (
    clear_cache,
    get_default_session,
    get_instrument,
    get_session_times,
    get_trading_day_boundaries,
    list_sessions,
    register_instrument,
)

# --- Fixtures ---

# Supabase-style row (matches instrument_full view output)
ES_ROW = {
    "symbol": "ES",
    "name": "E-mini S&P 500",
    "exchange": "CME",
    "type": "futures",
    "category": "index",
    "currency": "USD",
    "default_session": "ETH",
    "data_start": "2008-01-02",
    "data_end": "2026-02-11",
    "events": ["macro", "options"],
    "notes": None,
    "config": (
        '{"sessions": {"ETH": ["18:00", "17:00"], "RTH": ["09:30", "16:15"]},'
        ' "tick_size": 0.25, "tick_value": 12.5, "point_value": 50}'
    ),
    "exchange_timezone": "CT",
    "exchange_name": "Chicago Mercantile Exchange",
}

BRN_ROW = {
    "symbol": "BRN",
    "name": "Brent Crude Oil",
    "exchange": "ICEEUR",
    "type": "futures",
    "category": "energy",
    "currency": "USD",
    "default_session": "RTH",
    "data_start": "2010-01-04",
    "data_end": "2026-02-11",
    "events": ["macro", "oil"],
    "notes": "Known rollover offset vs TV",
    "config": {
        "sessions": {"ETH": ["20:00", "18:00"], "RTH": ["03:00", "14:30"]},
        "tick_size": 0.01,
        "tick_value": 10.0,
    },
    "exchange_timezone": "GMT",
    "exchange_name": "Intercontinental Exchange Europe",
}


@pytest.fixture(autouse=True)
def _setup_cache(_register_instruments):
    """Register test instruments before each test, restore after.

    Depends on conftest._register_instruments to ensure NQ is registered
    at session scope. We add ES/BRN, then restore to just NQ after.
    """
    from config.market.instruments import _CACHE

    saved = dict(_CACHE)
    register_instrument(ES_ROW)
    register_instrument(BRN_ROW)
    yield
    _CACHE.clear()
    _CACHE.update(saved)


# --- register_instrument / get_instrument ---


class TestRegisterAndGet:
    def test_registered_instrument_found(self):
        es = get_instrument("ES")
        assert es is not None
        assert es["name"] == "E-mini S&P 500"
        assert es["exchange"] == "CME"

    def test_case_insensitive(self):
        assert get_instrument("es") is not None
        assert get_instrument("Es") is not None

    def test_unknown_returns_none(self):
        assert get_instrument("UNKNOWN") is None

    def test_config_json_parsed(self):
        """Config JSON string is parsed and fields extracted."""
        es = get_instrument("ES")
        assert es["tick_size"] == 0.25
        assert es["tick_value"] == 12.5
        assert es["point_value"] == 50

    def test_config_dict_accepted(self):
        """Config can be a dict (not just JSON string)."""
        brn = get_instrument("BRN")
        assert brn["tick_size"] == 0.01

    def test_sessions_are_tuples(self):
        """Sessions arrays from Supabase are converted to tuples."""
        es = get_instrument("ES")
        assert es["sessions"]["ETH"] == ("18:00", "17:00")
        assert es["sessions"]["RTH"] == ("09:30", "16:15")
        assert isinstance(es["sessions"]["ETH"], tuple)

    def test_holidays_merged_from_exchange(self):
        """Holidays are looked up by exchange code."""
        es = get_instrument("ES")
        holidays = es["holidays"]
        assert "full_close" in holidays
        assert "christmas" in holidays["full_close"]
        assert "early_close" in holidays
        assert "christmas_eve" in holidays["early_close"]

    def test_eu_exchange_holidays(self):
        """European exchanges get EU holiday rules."""
        brn = get_instrument("BRN")
        holidays = brn["holidays"]
        assert "christmas" in holidays["full_close"]
        # EU doesn't have US-only holidays
        assert "thanksgiving" not in holidays["full_close"]
        assert "independence_day" not in holidays["full_close"]

    def test_notes_preserved(self):
        brn = get_instrument("BRN")
        assert brn["notes"] == "Known rollover offset vs TV"

    def test_events_preserved(self):
        es = get_instrument("ES")
        assert es["events"] == ["macro", "options"]
        brn = get_instrument("BRN")
        assert es["events"] == ["macro", "options"]
        assert brn["events"] == ["macro", "oil"]


# --- Session helpers ---


class TestSessionTimes:
    def test_rth(self):
        assert get_session_times("ES", "RTH") == ("09:30", "16:15")

    def test_eth(self):
        assert get_session_times("ES", "ETH") == ("18:00", "17:00")

    def test_case_insensitive(self):
        assert get_session_times("ES", "rth") == ("09:30", "16:15")

    def test_unknown_session(self):
        assert get_session_times("ES", "UNKNOWN") is None

    def test_unknown_instrument(self):
        assert get_session_times("UNKNOWN", "RTH") is None


class TestTradingDayBoundaries:
    def test_es(self):
        assert get_trading_day_boundaries("ES") == ("18:00", "17:00")

    def test_brn(self):
        assert get_trading_day_boundaries("BRN") == ("20:00", "18:00")

    def test_unknown(self):
        assert get_trading_day_boundaries("UNKNOWN") is None


class TestListSessions:
    def test_es_sessions(self):
        sessions = list_sessions("ES")
        assert "RTH" in sessions
        assert "ETH" in sessions
        assert len(sessions) == 2

    def test_unknown(self):
        assert list_sessions("UNKNOWN") == []


class TestDefaultSession:
    def test_es(self):
        assert get_default_session("ES") == "ETH"

    def test_brn(self):
        assert get_default_session("BRN") == "RTH"

    def test_unknown(self):
        assert get_default_session("UNKNOWN") == "RTH"


class TestClearCache:
    def test_clear(self):
        assert get_instrument("ES") is not None
        clear_cache()
        assert get_instrument("ES") is None
