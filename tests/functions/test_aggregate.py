"""Tests for aggregate functions."""

from barb.functions import FUNCTIONS


class TestAggregate:
    def test_mean(self, df):
        result = FUNCTIONS["mean"](df, df["close"])
        expected = sum([103, 101, 103, 106, 104, 100, 107, 105, 101, 102]) / 10
        assert abs(result - expected) < 0.01

    def test_sum(self, df):
        result = FUNCTIONS["sum"](df, df["volume"])
        assert result == 13000

    def test_count(self, df):
        assert FUNCTIONS["count"](df) == 10

    def test_max(self, df):
        assert FUNCTIONS["max"](df, df["close"]) == 107

    def test_min(self, df):
        assert FUNCTIONS["min"](df, df["close"]) == 100

    def test_median(self, df):
        result = FUNCTIONS["median"](df, df["close"])
        # sorted: 100, 101, 101, 102, 103, 103, 104, 105, 106, 107
        assert result == 103  # median of 10 values = avg of 5th and 6th

    def test_percentile(self, df):
        result = FUNCTIONS["percentile"](df, df["close"], 0.5)
        assert result == FUNCTIONS["median"](df, df["close"])

    def test_correlation(self, df):
        result = FUNCTIONS["correlation"](df, df["close"], df["close"])
        assert abs(result - 1.0) < 1e-10  # perfect self-correlation

    def test_last(self, df):
        assert FUNCTIONS["last"](df, df["close"]) == 102

    def test_pct(self, df):
        # close > 103: values 106, 104, 107, 105 = 4 out of 10
        result = FUNCTIONS["pct"](df, df["close"] > 103)
        assert abs(result - 0.4) < 1e-10

    def test_pct_all_true(self, df):
        result = FUNCTIONS["pct"](df, df["close"] > 0)
        assert abs(result - 1.0) < 1e-10

    def test_pct_none_true(self, df):
        result = FUNCTIONS["pct"](df, df["close"] > 9999)
        assert result == 0.0
