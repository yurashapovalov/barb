"""Tests for cumulative functions: cummax, cummin, cumsum."""

from barb.functions import FUNCTIONS


class TestCumulative:
    def test_cummax(self, df):
        result = FUNCTIONS["cummax"](df, df["close"])
        assert result.iloc[0] == 103
        assert result.iloc[3] == 106  # 106 is new max
        assert result.iloc[5] == 106  # still 106

    def test_cummin(self, df):
        result = FUNCTIONS["cummin"](df, df["close"])
        assert result.iloc[0] == 103
        assert result.iloc[5] == 100  # 100 is new min

    def test_cumsum(self, df):
        result = FUNCTIONS["cumsum"](df, df["volume"])
        assert result.iloc[0] == 1000
        assert result.iloc[1] == 2500
        assert result.iloc[2] == 3700
