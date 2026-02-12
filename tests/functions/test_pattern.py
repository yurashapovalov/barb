"""Tests for pattern functions."""

import numpy as np
import pandas as pd

from barb.functions import FUNCTIONS
from barb.functions.pattern import _falling, _pivothigh, _pivotlow, _rising, _valuewhen


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


# --- Rising / Falling ---


class TestRising:
    def test_basic(self):
        col = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        df = pd.DataFrame({"close": col})
        result = _rising(df, col, 3)
        # Need 3 consecutive rises: bar 3 (2<3<4) = True, bar 4 (3<4<5) = True
        assert result.iloc[3] is np.True_
        assert result.iloc[4] is np.True_

    def test_flat_is_not_rising(self):
        col = pd.Series([1.0, 2.0, 2.0, 3.0])
        df = pd.DataFrame({"close": col})
        result = _rising(df, col, 2)
        # bar 2: col[2]=2 > col[1]=2? No → False
        assert result.iloc[2] is np.False_

    def test_n1_default(self, df):
        result = _rising(df, df["close"], 1)
        # close: [103, 101, 103, 106, 104, 100, 107, 105, 101, 102]
        # rising(1): col > prev → [NaN, F, T, T, F, F, T, F, F, T]
        assert result.iloc[2] is np.True_  # 103 > 101
        assert result.iloc[4] is np.False_  # 104 > 106? No


class TestFalling:
    def test_basic(self):
        col = pd.Series([5.0, 4.0, 3.0, 2.0, 1.0])
        df = pd.DataFrame({"close": col})
        result = _falling(df, col, 3)
        assert result.iloc[3] is np.True_
        assert result.iloc[4] is np.True_

    def test_symmetry_with_rising(self):
        col = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        df = pd.DataFrame({"close": col})
        assert _rising(df, col, 2).iloc[-1] is np.True_
        assert _falling(df, col, 2).iloc[-1] is np.False_


# --- Valuewhen ---


class TestValuewhen:
    def test_most_recent(self):
        cond = pd.Series([True, False, True, False, False])
        col = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        df = pd.DataFrame({"close": col})
        result = _valuewhen(df, cond, col, 0)
        # Most recent true: bar 0 → 10, then bar 2 → 30
        assert result.iloc[0] == 10.0
        assert result.iloc[1] == 10.0  # last true was bar 0
        assert result.iloc[2] == 30.0  # bar 2 is true
        assert result.iloc[4] == 30.0  # still bar 2

    def test_previous_occurrence(self):
        cond = pd.Series([True, False, True, False, True])
        col = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        df = pd.DataFrame({"close": col})
        result = _valuewhen(df, cond, col, 1)
        # n=1: second most recent true
        # At bar 4: true occurrences at 0,2,4. n=1 → bar 2 → value 30
        assert result.iloc[4] == 30.0

    def test_nan_before_enough_occurrences(self):
        cond = pd.Series([False, False, True, False, False])
        col = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        df = pd.DataFrame({"close": col})
        result = _valuewhen(df, cond, col, 1)
        # Only one occurrence at bar 2, n=1 needs two → NaN
        assert pd.isna(result.iloc[4])


# --- Pivot High / Low ---


class TestPivotHigh:
    def test_detects_peak(self):
        # Clear peak at bar 5 (value 110)
        high = pd.Series([100, 102, 105, 108, 109, 110, 108, 105, 103, 101, 100.0])
        df = pd.DataFrame(
            {
                "high": high,
                "low": high - 2,
                "open": high - 1,
                "close": high - 0.5,
                "volume": [100] * 11,
            }
        )
        result = _pivothigh(df, 3, 3)
        # Peak at bar 5, reported at bar 5+3=8
        assert result.iloc[8] == 110.0
        # Other bars should be NaN
        assert pd.isna(result.iloc[5])

    def test_no_pivot_in_monotone(self):
        high = pd.Series([float(i) for i in range(20)])
        df = pd.DataFrame(
            {
                "high": high,
                "low": high - 1,
                "open": high - 0.5,
                "close": high,
                "volume": [100] * 20,
            }
        )
        result = _pivothigh(df, 5, 5)
        assert result.isna().all()


class TestPivotLow:
    def test_detects_trough(self):
        # Clear trough at bar 5 (value 90)
        low = pd.Series([100, 98, 95, 93, 91, 90, 92, 95, 97, 99, 100.0])
        df = pd.DataFrame(
            {
                "low": low,
                "high": low + 2,
                "open": low + 1,
                "close": low + 0.5,
                "volume": [100] * 11,
            }
        )
        result = _pivotlow(df, 3, 3)
        # Trough at bar 5, reported at bar 8
        assert result.iloc[8] == 90.0

    def test_symmetry_with_pivothigh(self):
        """Pivot low on inverted data should find same positions as pivot high."""
        high = pd.Series([100, 105, 110, 105, 100, 95, 100, 105, 110, 105, 100.0])
        df_high = pd.DataFrame(
            {
                "high": high,
                "low": high - 2,
                "open": high,
                "close": high,
                "volume": [100] * 11,
            }
        )
        df_low = pd.DataFrame(
            {
                "low": -high,
                "high": -high + 2,
                "open": -high,
                "close": -high,
                "volume": [100] * 11,
            }
        )
        ph = _pivothigh(df_high, 2, 2)
        pl = _pivotlow(df_low, 2, 2)
        # Pivots should appear at same bars
        assert ph.notna().sum() > 0
        assert (ph.notna() == pl.notna()).all()
