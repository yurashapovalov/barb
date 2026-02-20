"""Tests for time functions."""

from barb.functions import FUNCTIONS


class TestTime:
    def test_year(self, df):
        result = FUNCTIONS["year"](df)
        assert result.iloc[0] == 2024

    def test_quarter(self, df):
        result = FUNCTIONS["quarter"](df)
        assert result.iloc[0] == 1  # Q1

    def test_month(self, df):
        result = FUNCTIONS["month"](df)
        assert result.iloc[0] == 1  # January

    def test_day_of_month(self, df):
        result = FUNCTIONS["day_of_month"](df)
        assert result.iloc[0] == 2  # Jan 2

    def test_dayofweek(self, df):
        result = FUNCTIONS["dayofweek"](df)
        # Jan 2, 2024 is Tuesday (1)
        assert result.iloc[0] == 1
        assert result.iloc[1] == 2  # Wednesday

    def test_hour(self, df):
        result = FUNCTIONS["hour"](df)
        # Daily bars at midnight
        assert result.iloc[0] == 0

    def test_minute(self, df):
        result = FUNCTIONS["minute"](df)
        # Daily bars at midnight → minute is 0
        assert result.iloc[0] == 0
