"""Tests for trading convenience functions."""

import pandas as pd

from barb.functions import FUNCTIONS


class TestPrice:
    def test_gap(self, df):
        result = FUNCTIONS["gap"](df)
        # gap = open - prev(close). First bar has NaN prev close.
        assert pd.isna(result.iloc[0])
        # bar 1: open=102, prev close=103 → gap=-1
        assert result.iloc[1] == -1

    def test_gap_pct(self, df):
        result = FUNCTIONS["gap_pct"](df)
        assert pd.isna(result.iloc[0])
        # bar 1: (102 - 103) / 103 * 100 ≈ -0.9709
        assert abs(result.iloc[1] - (-1 / 103 * 100)) < 0.01

    def test_change(self, df):
        result = FUNCTIONS["change"](df, df["close"])
        assert pd.isna(result.iloc[0])
        # bar 1: 101 - 103 = -2
        assert result.iloc[1] == -2

    def test_change_n(self, df):
        result = FUNCTIONS["change"](df, df["close"], 2)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        # bar 2: 103 - 103 = 0
        assert result.iloc[2] == 0

    def test_change_pct(self, df):
        result = FUNCTIONS["change_pct"](df, df["close"])
        assert pd.isna(result.iloc[0])
        # bar 1: (101 - 103) / 103 * 100
        expected = (101 - 103) / 103 * 100
        assert abs(result.iloc[1] - expected) < 0.01

    def test_range(self, df):
        result = FUNCTIONS["range"](df)
        # bar 0: 105 - 98 = 7
        assert result.iloc[0] == 7
        # bar 3: 108 - 103 = 5
        assert result.iloc[3] == 5

    def test_range_pct(self, df):
        result = FUNCTIONS["range_pct"](df)
        # bar 0: (105 - 98) / 98 * 100
        expected = 7 / 98 * 100
        assert abs(result.iloc[0] - expected) < 0.01

    def test_midpoint(self, df):
        result = FUNCTIONS["midpoint"](df)
        # bar 0: (105 + 98) / 2 = 101.5
        assert result.iloc[0] == 101.5

    def test_typical_price(self, df):
        result = FUNCTIONS["typical_price"](df)
        # bar 0: (105 + 98 + 103) / 3 = 102.0
        assert abs(result.iloc[0] - 102.0) < 0.01


class TestCandle:
    def test_body(self, df):
        result = FUNCTIONS["body"](df)
        # bar 0: 103 - 100 = 3 (green)
        assert result.iloc[0] == 3
        # bar 1: 101 - 102 = -1 (red)
        assert result.iloc[1] == -1

    def test_body_pct(self, df):
        result = FUNCTIONS["body_pct"](df)
        # bar 0: (103 - 100) / 100 * 100 = 3.0%
        assert result.iloc[0] == 3.0

    def test_upper_wick(self, df):
        result = FUNCTIONS["upper_wick"](df)
        # bar 0: high=105, max(open=100, close=103)=103 → 105-103=2
        assert result.iloc[0] == 2
        # bar 1: high=106, max(open=102, close=101)=102 → 106-102=4
        assert result.iloc[1] == 4

    def test_lower_wick(self, df):
        result = FUNCTIONS["lower_wick"](df)
        # bar 0: min(open=100, close=103)=100, low=98 → 100-98=2
        assert result.iloc[0] == 2
        # bar 1: min(open=102, close=101)=101, low=100 → 101-100=1
        assert result.iloc[1] == 1

    def test_green(self, df):
        result = FUNCTIONS["green"](df)
        # close > open: [T, F, T, T, T, T, T, F, F, T]
        assert result.iloc[0]
        assert not result.iloc[1]

    def test_red(self, df):
        result = FUNCTIONS["red"](df)
        # close < open: [F, T, F, F, F, F, F, T, T, F]
        assert not result.iloc[0]
        assert result.iloc[1]

    def test_doji(self, df):
        result = FUNCTIONS["doji"](df)
        # bar 0: body=3, range=7 → 3/7=0.43 > 0.1 → not doji
        assert not result.iloc[0]

    def test_doji_custom_threshold(self, df):
        result = FUNCTIONS["doji"](df, 0.5)
        # bar 0: 3/7=0.43 < 0.5 → doji with relaxed threshold
        assert result.iloc[0]

    def test_inside_bar(self, df):
        result = FUNCTIONS["inside_bar"](df)
        assert not result.iloc[1]
        # bar 2: high=104 < 106 and low=99 < 100 → low not inside → False
        assert not result.iloc[2]

    def test_outside_bar(self, df):
        result = FUNCTIONS["outside_bar"](df)
        # bar 1: high=106 > 105 and low=100 > 98 → low not lower → False
        assert not result.iloc[1]


class TestSignal:
    def test_crossover(self):
        idx = pd.date_range("2024-01-01", periods=5, freq="D")
        a = pd.Series([1, 2, 3, 2, 4], index=idx, dtype=float)
        b = pd.Series([2, 2, 2, 3, 3], index=idx, dtype=float)
        df = pd.DataFrame({"a": a, "b": b}, index=idx)
        result = FUNCTIONS["crossover"](df, a, b)
        # bar 0: NaN (no prev)
        # bar 1: prev a=1 <= prev b=2, a=2 <= b=2 → False (not strictly >)
        # bar 2: prev a=2 <= prev b=2, a=3 > b=2 → True (crossover!)
        # bar 3: prev a=3 > prev b=2 → False (was already above)
        # bar 4: prev a=2 <= prev b=3, a=4 > b=3 → True
        assert result.iloc[2]
        assert not result.iloc[3]
        assert result.iloc[4]

    def test_crossunder(self):
        idx = pd.date_range("2024-01-01", periods=5, freq="D")
        a = pd.Series([3, 2, 1, 3, 2], index=idx, dtype=float)
        b = pd.Series([2, 2, 2, 2, 3], index=idx, dtype=float)
        df = pd.DataFrame({"a": a, "b": b}, index=idx)
        result = FUNCTIONS["crossunder"](df, a, b)
        # bar 2: prev a=2 >= prev b=2, a=1 < b=2 → True (crossunder!)
        # bar 4: prev a=3 >= prev b=2, a=2 < b=3 → True
        assert result.iloc[2]
        assert not result.iloc[3]
        assert result.iloc[4]

    def test_crossover_no_false_positives(self):
        """When a is always above b, no crossover signals."""
        idx = pd.date_range("2024-01-01", periods=4, freq="D")
        a = pd.Series([5, 6, 7, 8], index=idx, dtype=float)
        b = pd.Series([1, 2, 3, 4], index=idx, dtype=float)
        df = pd.DataFrame({"a": a, "b": b}, index=idx)
        result = FUNCTIONS["crossover"](df, a, b)
        # a always > b, prev a always > prev b → no crossover
        assert not result.iloc[1]
        assert not result.iloc[2]
        assert not result.iloc[3]
