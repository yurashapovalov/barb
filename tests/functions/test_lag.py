"""Tests for lag functions: prev, next."""

import pandas as pd

from barb.functions import FUNCTIONS


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
