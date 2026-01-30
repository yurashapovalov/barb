"""Tests for config/market/events.py — event date calculations."""

from datetime import date

from config.market.events import (
    get_event_dates,
    get_event_type,
    get_event_types_for_instrument,
    get_events_for_date,
    get_nfp_date,
    get_opex_date,
    get_vix_expiration,
    is_high_impact_day,
)


class TestOpexDate:
    """Third Friday of month."""

    def test_jan_2024(self):
        assert get_opex_date(2024, 1) == date(2024, 1, 19)

    def test_mar_2024(self):
        assert get_opex_date(2024, 3) == date(2024, 3, 15)

    def test_dec_2024(self):
        assert get_opex_date(2024, 12) == date(2024, 12, 20)


class TestNfpDate:
    """First Friday of month."""

    def test_jan_2024(self):
        assert get_nfp_date(2024, 1) == date(2024, 1, 5)

    def test_feb_2024(self):
        assert get_nfp_date(2024, 2) == date(2024, 2, 2)

    def test_mar_2024(self):
        # March 1 2024 = Friday
        assert get_nfp_date(2024, 3) == date(2024, 3, 1)


class TestVixExpiration:
    """Wednesday before third Friday."""

    def test_jan_2024(self):
        # OPEX Jan 19 → VIX Jan 17 (Wed)
        assert get_vix_expiration(2024, 1) == date(2024, 1, 17)

    def test_mar_2024(self):
        # OPEX Mar 15 → VIX Mar 13 (Wed)
        assert get_vix_expiration(2024, 3) == date(2024, 3, 13)


class TestEventDates:
    def test_opex_full_year(self):
        dates = get_event_dates("opex", date(2024, 1, 1), date(2024, 12, 31))
        assert len(dates) == 12  # One per month

    def test_quad_witching(self):
        dates = get_event_dates("quad_witching", date(2024, 1, 1), date(2024, 12, 31))
        assert len(dates) == 4  # Mar, Jun, Sep, Dec
        assert all(d.month in (3, 6, 9, 12) for d in dates)

    def test_nfp_full_year(self):
        dates = get_event_dates("nfp", date(2024, 1, 1), date(2024, 12, 31))
        assert len(dates) == 12

    def test_vix_exp(self):
        dates = get_event_dates("vix_exp", date(2024, 1, 1), date(2024, 12, 31))
        assert len(dates) == 12

    def test_non_calculable_event(self):
        # FOMC dates can't be calculated from rules
        dates = get_event_dates("fomc", date(2024, 1, 1), date(2024, 12, 31))
        assert dates == []

    def test_date_range_filtering(self):
        dates = get_event_dates("opex", date(2024, 3, 1), date(2024, 3, 31))
        assert len(dates) == 1
        assert dates[0] == date(2024, 3, 15)


class TestEventsForDate:
    def test_opex_day(self):
        # Jan 19 2024 = regular OPEX (not quad witching month)
        events = get_events_for_date(date(2024, 1, 19))
        names = [e.name for e in events]
        assert "Options Expiration" in names

    def test_quad_witching_day(self):
        # Mar 15 2024 = quad witching (3rd Friday of March)
        events = get_events_for_date(date(2024, 3, 15))
        names = [e.name for e in events]
        assert "Quad Witching" in names
        # Should NOT also list regular OPEX
        assert "Options Expiration" not in names

    def test_nfp_day(self):
        events = get_events_for_date(date(2024, 1, 5))
        names = [e.name for e in events]
        assert "Non-Farm Payrolls" in names

    def test_vix_expiration_day(self):
        events = get_events_for_date(date(2024, 1, 17))
        names = [e.name for e in events]
        assert "VIX Expiration" in names

    def test_no_events(self):
        # Random Tuesday with no scheduled events
        events = get_events_for_date(date(2024, 1, 9))
        assert events == []


class TestHighImpactDay:
    def test_opex_is_high_impact(self):
        assert is_high_impact_day("NQ", date(2024, 1, 19)) is True

    def test_nfp_is_high_impact(self):
        assert is_high_impact_day("NQ", date(2024, 1, 5)) is True

    def test_regular_day_not_high_impact(self):
        assert is_high_impact_day("NQ", date(2024, 1, 9)) is False


class TestEventTypes:
    def test_get_event_type_known(self):
        event = get_event_type("fomc")
        assert event is not None
        assert event.name == "FOMC Rate Decision"

    def test_get_event_type_unknown(self):
        assert get_event_type("nonexistent") is None

    def test_nq_event_types(self):
        events = get_event_types_for_instrument("NQ")
        # NQ has macro + options events
        names = {e.id for e in events}
        assert "fomc" in names
        assert "opex" in names
        # NQ should NOT have oil events
        assert "eia_crude" not in names
