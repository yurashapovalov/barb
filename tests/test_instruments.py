"""Tests for config/market/instruments.py — instrument configuration."""

from config.market.instruments import (
    get_default_session,
    get_instrument,
    get_maintenance_window,
    get_session_times,
    get_trading_day_boundaries,
    is_calendar_day,
    list_sessions,
)


class TestGetInstrument:
    def test_nq_exists(self):
        nq = get_instrument("NQ")
        assert nq is not None
        assert nq["name"] == "Nasdaq 100 E-mini"
        assert nq["exchange"] == "CME"

    def test_case_insensitive(self):
        assert get_instrument("nq") is not None
        assert get_instrument("Nq") is not None

    def test_unknown_returns_none(self):
        assert get_instrument("UNKNOWN") is None


class TestSessionTimes:
    def test_rth(self):
        assert get_session_times("NQ", "RTH") == ("09:30", "17:00")

    def test_eth(self):
        assert get_session_times("NQ", "ETH") == ("18:00", "17:00")

    def test_overnight(self):
        assert get_session_times("NQ", "OVERNIGHT") == ("18:00", "09:30")

    def test_case_insensitive(self):
        assert get_session_times("NQ", "rth") == ("09:30", "17:00")

    def test_unknown_session(self):
        assert get_session_times("NQ", "UNKNOWN") is None

    def test_unknown_instrument(self):
        assert get_session_times("UNKNOWN", "RTH") is None


class TestTradingDayBoundaries:
    def test_nq_boundaries(self):
        # ETH = full trading day
        assert get_trading_day_boundaries("NQ") == ("18:00", "17:00")

    def test_unknown(self):
        assert get_trading_day_boundaries("UNKNOWN") is None


class TestIsCalendarDay:
    def test_nq_not_calendar_day(self):
        # NQ trades 18:00-17:00, not 00:00-23:59
        assert is_calendar_day("NQ") is False

    def test_unknown_defaults_true(self):
        assert is_calendar_day("UNKNOWN") is True


class TestMaintenance:
    def test_nq_maintenance(self):
        assert get_maintenance_window("NQ") == ("17:00", "18:00")

    def test_unknown(self):
        assert get_maintenance_window("UNKNOWN") is None


class TestListSessions:
    def test_nq_sessions(self):
        sessions = list_sessions("NQ")
        assert "RTH" in sessions
        assert "ETH" in sessions
        assert "OVERNIGHT" in sessions
        assert len(sessions) == 9

    def test_unknown(self):
        assert list_sessions("UNKNOWN") == []


class TestDefaultSession:
    def test_nq(self):
        assert get_default_session("NQ") == "RTH"

    def test_unknown(self):
        assert get_default_session("UNKNOWN") == "RTH"
