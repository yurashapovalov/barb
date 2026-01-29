"""Tests for Barb Script functions."""

import numpy as np
import pandas as pd
import pytest

from barb.functions import FUNCTIONS


@pytest.fixture
def df():
    """DataFrame with DatetimeIndex for function tests."""
    dates = pd.date_range("2024-01-02", periods=10, freq="D")  # Tue Jan 2
    return pd.DataFrame({
        "open": [100, 102, 101, 105, 103, 99, 104, 106, 102, 100],
        "high": [105, 106, 104, 108, 107, 103, 108, 110, 106, 104],
        "low": [98, 100, 99, 103, 101, 97, 102, 104, 100, 98],
        "close": [103, 101, 103, 106, 104, 100, 107, 105, 101, 102],
        "volume": [1000, 1500, 1200, 2000, 800, 1100, 1800, 900, 1400, 1300],
    }, index=dates, dtype=float)


# --- Scalar Functions ---

class TestScalar:
    def test_abs(self, df):
        result = FUNCTIONS["abs"](df, df["close"] - df["open"])
        assert list(result) == [3, 1, 2, 1, 1, 1, 3, 1, 1, 2]

    def test_sign(self, df):
        result = FUNCTIONS["sign"](df, df["close"] - df["open"])
        assert list(result) == [1, -1, 1, 1, 1, 1, 1, -1, -1, 1]

    def test_sqrt(self, df):
        result = FUNCTIONS["sqrt"](df, pd.Series([4.0, 9.0, 16.0], index=df.index[:3]))
        assert list(result) == [2.0, 3.0, 4.0]

    def test_round(self, df):
        vals = pd.Series([1.234, 5.678, 9.012], index=df.index[:3])
        result = FUNCTIONS["round"](df, vals, 1)
        assert list(result) == [1.2, 5.7, 9.0]

    def test_if(self, df):
        cond = df["close"] > df["open"]
        result = FUNCTIONS["if"](df, cond, 1, 0)
        # close > open: [T, F, T, T, T, T, T, F, F, T]
        assert list(result) == [1, 0, 1, 1, 1, 1, 1, 0, 0, 1]

    def test_if_series_values(self, df):
        cond = df["close"] > df["open"]
        result = FUNCTIONS["if"](df, cond, df["close"], df["open"])
        # Where close > open: use close, else use open
        assert result.iloc[0] == 103  # close > open → close
        assert result.iloc[1] == 102  # close < open → open


# --- Lag Functions ---

class TestLag:
    def test_prev(self, df):
        result = FUNCTIONS["prev"](df, df["close"])
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] == 103
        assert result.iloc[2] == 101

    def test_prev_n(self, df):
        result = FUNCTIONS["prev"](df, df["close"], 2)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert result.iloc[2] == 103

    def test_next(self, df):
        result = FUNCTIONS["next"](df, df["close"])
        assert result.iloc[0] == 101
        assert pd.isna(result.iloc[-1])

    def test_next_n(self, df):
        result = FUNCTIONS["next"](df, df["close"], 2)
        assert result.iloc[0] == 103
        assert pd.isna(result.iloc[-1])
        assert pd.isna(result.iloc[-2])


# --- Window Functions ---

class TestWindow:
    def test_rolling_mean(self, df):
        result = FUNCTIONS["rolling_mean"](df, df["close"], 3)
        # First 2 are NaN, third = mean(103, 101, 103) = 102.33...
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert abs(result.iloc[2] - 102.333) < 0.01

    def test_rolling_sum(self, df):
        result = FUNCTIONS["rolling_sum"](df, df["volume"], 3)
        assert pd.isna(result.iloc[1])
        assert result.iloc[2] == 3700  # 1000 + 1500 + 1200

    def test_rolling_max(self, df):
        result = FUNCTIONS["rolling_max"](df, df["high"], 3)
        assert result.iloc[2] == 106  # max(105, 106, 104)

    def test_rolling_min(self, df):
        result = FUNCTIONS["rolling_min"](df, df["low"], 3)
        assert result.iloc[2] == 98  # min(98, 100, 99)

    def test_ema(self, df):
        result = FUNCTIONS["ema"](df, df["close"], 3)
        # EMA should not have NaN (ewm starts from first value)
        assert not pd.isna(result.iloc[0])
        assert len(result) == 10

    def test_rolling_count(self, df):
        cond = df["close"] > df["open"]
        result = FUNCTIONS["rolling_count"](df, cond, 3)
        # cond: [T, F, T, T, T, T, T, F, F, T]
        # rolling 3: NaN, NaN, 2, 2, 3, 3, 3, 2, 1, 1
        assert result.iloc[4] == 3  # all 3 true in window


# --- Cumulative Functions ---

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


# --- Pattern Functions ---

class TestPattern:
    def test_streak(self, df):
        cond = df["close"] > df["open"]
        result = FUNCTIONS["streak"](df, cond)
        # cond: [T, F, T, T, T, T, T, F, F, T]
        assert result.iloc[0] == 1  # first true
        assert result.iloc[1] == 0  # false resets
        assert result.iloc[6] == 5  # 5 consecutive true
        assert result.iloc[7] == 0  # false resets

    def test_bars_since(self, df):
        cond = df["volume"] >= 2000
        result = FUNCTIONS["bars_since"](df, cond)
        # volume >= 2000 at index 3 only
        assert pd.isna(result.iloc[0])  # never true yet
        assert result.iloc[3] == 0  # just happened
        assert result.iloc[5] == 2  # 2 bars since

    def test_rank(self, df):
        result = FUNCTIONS["rank"](df, df["close"])
        # rank returns percentile (0-1)
        assert 0 <= result.iloc[0] <= 1
        # Highest close (107) should have highest rank
        assert result.iloc[6] == 1.0


# --- Aggregate Functions ---

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


# --- Time Functions ---

class TestTime:
    def test_dayofweek(self, df):
        result = FUNCTIONS["dayofweek"](df)
        # Jan 2, 2024 is Tuesday (1)
        assert result.iloc[0] == 1
        assert result.iloc[1] == 2  # Wednesday

    def test_hour(self, df):
        result = FUNCTIONS["hour"](df)
        # Daily bars at midnight
        assert result.iloc[0] == 0

    def test_month(self, df):
        result = FUNCTIONS["month"](df)
        assert result.iloc[0] == 1  # January

    def test_year(self, df):
        result = FUNCTIONS["year"](df)
        assert result.iloc[0] == 2024

    def test_day(self, df):
        result = FUNCTIONS["day"](df)
        assert result.iloc[0] == 2  # Jan 2

    def test_dayname(self, df):
        result = FUNCTIONS["dayname"](df)
        # Jan 2, 2024 is Tuesday
        assert result.iloc[0] == "Tuesday"
        assert result.iloc[1] == "Wednesday"

    def test_monthname(self, df):
        result = FUNCTIONS["monthname"](df)
        assert result.iloc[0] == "January"

    def test_quarter(self, df):
        result = FUNCTIONS["quarter"](df)
        assert result.iloc[0] == 1  # Q1
