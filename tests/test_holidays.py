"""Tests for config/market/holidays.py — holiday date calculations."""

from datetime import date

from config.market.holidays import (
    get_close_time,
    get_day_type,
    get_holiday_date,
    get_holidays_for_year,
    is_trading_day,
)


class TestHolidayDates:
    """Verify holiday date calculations against known dates."""

    # Fixed holidays with observed adjustment
    def test_new_year_2025_wednesday(self):
        assert get_holiday_date("new_year", 2025) == date(2025, 1, 1)

    def test_new_year_2023_sunday_observed_monday(self):
        # Jan 1 2023 = Sunday → observed Monday Jan 2
        assert get_holiday_date("new_year", 2023) == date(2023, 1, 2)

    def test_christmas_2021_saturday_observed_friday(self):
        # Dec 25 2021 = Saturday → observed Friday Dec 24
        assert get_holiday_date("christmas", 2021) == date(2021, 12, 24)

    def test_christmas_2024_wednesday(self):
        assert get_holiday_date("christmas", 2024) == date(2024, 12, 25)

    def test_independence_day_2020_saturday_observed_friday(self):
        # July 4 2020 = Saturday → observed Friday July 3
        assert get_holiday_date("independence_day", 2020) == date(2020, 7, 3)

    def test_juneteenth_2022_sunday_observed_monday(self):
        # June 19 2022 = Sunday → observed Monday June 20
        assert get_holiday_date("juneteenth", 2022) == date(2022, 6, 20)

    # Nth weekday holidays
    def test_mlk_day_2024(self):
        # 3rd Monday of January 2024 = Jan 15
        assert get_holiday_date("mlk_day", 2024) == date(2024, 1, 15)

    def test_presidents_day_2024(self):
        # 3rd Monday of February 2024 = Feb 19
        assert get_holiday_date("presidents_day", 2024) == date(2024, 2, 19)

    def test_memorial_day_2024(self):
        # Last Monday of May 2024 = May 27
        assert get_holiday_date("memorial_day", 2024) == date(2024, 5, 27)

    def test_labor_day_2024(self):
        # 1st Monday of September 2024 = Sep 2
        assert get_holiday_date("labor_day", 2024) == date(2024, 9, 2)

    def test_thanksgiving_2024(self):
        # 4th Thursday of November 2024 = Nov 28
        assert get_holiday_date("thanksgiving", 2024) == date(2024, 11, 28)

    # Easter-based
    def test_good_friday_2024(self):
        # Easter 2024 = March 31 → Good Friday = March 29
        assert get_holiday_date("good_friday", 2024) == date(2024, 3, 29)

    def test_good_friday_2025(self):
        # Easter 2025 = April 20 → Good Friday = April 18
        assert get_holiday_date("good_friday", 2025) == date(2025, 4, 18)

    # Early close days
    def test_black_friday_2024(self):
        # Day after Thanksgiving (Nov 28) = Nov 29
        assert get_holiday_date("black_friday", 2024) == date(2024, 11, 29)

    def test_christmas_eve_2024_tuesday(self):
        assert get_holiday_date("christmas_eve", 2024) == date(2024, 12, 24)

    def test_christmas_eve_2022_saturday_observed_friday(self):
        # Dec 24 2022 = Saturday → Friday Dec 23
        assert get_holiday_date("christmas_eve", 2022) == date(2022, 12, 23)

    def test_independence_day_eve_2025_thursday(self):
        assert get_holiday_date("independence_day_eve", 2025) == date(2025, 7, 3)

    def test_new_year_eve_2024_tuesday(self):
        assert get_holiday_date("new_year_eve", 2024) == date(2024, 12, 31)

    def test_unknown_rule(self):
        assert get_holiday_date("nonexistent", 2024) is None


class TestDayType:
    def test_regular_day(self):
        assert get_day_type("NQ", "2024-03-05") == "regular"

    def test_christmas_closed(self):
        assert get_day_type("NQ", "2024-12-25") == "closed"

    def test_black_friday_early_close(self):
        assert get_day_type("NQ", "2024-11-29") == "early_close"

    def test_accepts_date_object(self):
        assert get_day_type("NQ", date(2024, 12, 25)) == "closed"

    def test_unknown_instrument(self):
        assert get_day_type("UNKNOWN", "2024-12-25") == "regular"


class TestCloseTime:
    def test_regular_day(self):
        assert get_close_time("NQ", "2024-03-05") == "17:00"

    def test_early_close_day(self):
        # Black Friday 2024 early close at 13:15
        assert get_close_time("NQ", "2024-11-29") == "13:15"

    def test_closed_day(self):
        assert get_close_time("NQ", "2024-12-25") is None


class TestIsTradingDay:
    def test_regular_weekday(self):
        assert is_trading_day("NQ", "2024-03-05") is True

    def test_saturday(self):
        assert is_trading_day("NQ", "2024-03-02") is False

    def test_sunday(self):
        assert is_trading_day("NQ", "2024-03-03") is False

    def test_holiday(self):
        assert is_trading_day("NQ", "2024-12-25") is False

    def test_early_close_is_trading_day(self):
        # Early close is still a trading day
        assert is_trading_day("NQ", "2024-11-29") is True


class TestHolidaysForYear:
    def test_nq_2024_full_close_count(self):
        holidays = get_holidays_for_year("NQ", 2024)
        # 10 full close holidays
        assert len(holidays["full_close"]) == 10

    def test_nq_2024_early_close_count(self):
        holidays = get_holidays_for_year("NQ", 2024)
        # 4 early close days
        assert len(holidays["early_close"]) == 4

    def test_unknown_instrument(self):
        holidays = get_holidays_for_year("UNKNOWN", 2024)
        assert holidays == {"full_close": [], "early_close": []}
