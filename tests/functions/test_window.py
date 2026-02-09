"""Tests for rolling window functions: rolling_mean/sum/max/min/std/count, ema."""

import pandas as pd

from barb.functions import FUNCTIONS


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
