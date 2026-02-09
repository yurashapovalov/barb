"""Tests for pattern functions: streak, bars_since, rank."""

import pandas as pd

from barb.functions import FUNCTIONS


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
