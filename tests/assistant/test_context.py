"""Tests for assistant/prompt/context.py — market context builders."""

import pytest

from assistant.prompt.context import (
    build_event_context,
    build_holiday_context,
    build_instrument_context,
)

# --- Fixtures ---


@pytest.fixture
def nq_config():
    """NQ-like config for testing."""
    return {
        "symbol": "NQ",
        "name": "Nasdaq 100 E-mini",
        "exchange": "CME",
        "data_start": "2008-01-02",
        "data_end": "2026-02-06",
        "tick_size": 0.25,
        "tick_value": 5.0,
        "point_value": 20.0,
        "default_session": "RTH",
        "sessions": {
            "ETH": ("18:00", "17:00"),
            "RTH": ("09:30", "17:00"),
        },
        "maintenance": ("17:00", "18:00"),
        "holidays": {
            "full_close": [
                "new_year",
                "mlk_day",
                "presidents_day",
                "good_friday",
                "memorial_day",
                "juneteenth",
                "independence_day",
                "labor_day",
                "thanksgiving",
                "christmas",
            ],
            "early_close": {
                "christmas_eve": "13:15",
                "black_friday": "13:15",
            },
        },
        "events": ["macro", "options"],
    }


@pytest.fixture
def minimal_config():
    """Minimal config — just symbol and sessions."""
    return {
        "symbol": "TEST",
        "name": "Test Instrument",
        "exchange": "TEST_EX",
        "data_start": "2020-01-01",
        "data_end": "2025-01-01",
        "tick_size": 1.0,
        "tick_value": 1.0,
        "default_session": "ETH",
        "sessions": {
            "ETH": ("00:00", "23:59"),
        },
    }


# --- build_instrument_context ---


class TestBuildInstrumentContext:
    def test_contains_symbol_and_name(self, nq_config):
        result = build_instrument_context(nq_config)
        assert "NQ" in result
        assert "Nasdaq 100 E-mini" in result

    def test_contains_exchange(self, nq_config):
        result = build_instrument_context(nq_config)
        assert "CME" in result

    def test_contains_sessions(self, nq_config):
        result = build_instrument_context(nq_config)
        assert "ETH" in result
        assert "18:00-17:00" in result
        assert "RTH" in result
        assert "09:30-17:00" in result

    def test_contains_tick_info(self, nq_config):
        result = build_instrument_context(nq_config)
        assert "0.25" in result
        assert "$5.0 per tick" in result
        assert "$20.0 per point" in result

    def test_contains_data_range(self, nq_config):
        result = build_instrument_context(nq_config)
        assert "2008-01-02" in result
        assert "2026-02-06" in result

    def test_contains_maintenance(self, nq_config):
        result = build_instrument_context(nq_config)
        assert "Maintenance" in result
        assert "17:00-18:00" in result

    def test_no_maintenance_when_absent(self, minimal_config):
        result = build_instrument_context(minimal_config)
        assert "Maintenance" not in result

    def test_xml_tags(self, nq_config):
        result = build_instrument_context(nq_config)
        assert result.startswith("<instrument>")
        assert result.endswith("</instrument>")

    def test_notes_when_present(self, nq_config):
        nq_config["notes"] = "Known rollover offset"
        result = build_instrument_context(nq_config)
        assert "Note: Known rollover offset" in result

    def test_no_notes_when_absent(self, nq_config):
        result = build_instrument_context(nq_config)
        assert "Note:" not in result

    def test_no_point_value(self, minimal_config):
        result = build_instrument_context(minimal_config)
        assert "$1.0 per tick" in result
        assert "per point" not in result


# --- build_holiday_context ---


class TestBuildHolidayContext:
    def test_contains_holiday_names(self, nq_config):
        result = build_holiday_context(nq_config)
        assert "New Year's Day" in result
        assert "Christmas Day" in result
        assert "Thanksgiving" in result

    def test_contains_early_close(self, nq_config):
        result = build_holiday_context(nq_config)
        assert "Christmas Eve" in result
        assert "13:15" in result
        assert "Black Friday" in result

    def test_contains_observation_rule(self, nq_config):
        result = build_holiday_context(nq_config)
        assert "Saturday" in result
        assert "Sunday" in result

    def test_xml_tags(self, nq_config):
        result = build_holiday_context(nq_config)
        assert "<holidays>" in result
        assert "</holidays>" in result

    def test_empty_when_no_holidays(self, minimal_config):
        result = build_holiday_context(minimal_config)
        assert result == ""

    def test_empty_holidays_dict(self):
        config = {"holidays": {}}
        result = build_holiday_context(config)
        assert result == ""

    def test_only_full_close(self):
        config = {"holidays": {"full_close": ["christmas"]}}
        result = build_holiday_context(config)
        assert "Christmas Day" in result
        assert "Early close" not in result

    def test_only_early_close(self):
        config = {"holidays": {"early_close": {"christmas_eve": "13:15"}}}
        result = build_holiday_context(config)
        assert "Christmas Eve (13:15)" in result
        assert "Market closed" not in result


# --- build_event_context ---


class TestBuildEventContext:
    def test_contains_high_impact(self, nq_config):
        result = build_event_context(nq_config)
        assert "FOMC" in result
        assert "Non-Farm Payrolls" in result
        assert "CPI" in result

    def test_contains_medium_impact(self, nq_config):
        result = build_event_context(nq_config)
        assert "Medium impact" in result
        assert "PPI" in result

    def test_contains_date_hints(self, nq_config):
        result = build_event_context(nq_config)
        assert "1st Friday" in result
        assert "3rd Friday" in result

    def test_xml_tags(self, nq_config):
        result = build_event_context(nq_config)
        assert "<events>" in result
        assert "</events>" in result

    def test_empty_when_no_symbol(self):
        result = build_event_context({})
        assert result == ""

    def test_contains_quad_witching(self, nq_config):
        result = build_event_context(nq_config)
        assert "Quad Witching" in result

    def test_event_times(self, nq_config):
        result = build_event_context(nq_config)
        # FOMC has typical_time
        assert "14:00 ET" in result
        # NFP has typical_time
        assert "08:30 ET" in result
