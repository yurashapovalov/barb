"""Tests for scalar functions: abs, log, sqrt, sign, round, if."""

import pandas as pd

from barb.functions import FUNCTIONS


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
