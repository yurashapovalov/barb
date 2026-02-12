"""Tests for rolling window functions."""

import numpy as np
import pandas as pd
import pytest

from barb.functions import FUNCTIONS
from barb.functions.window import _hma, _rma, _vwma, _wma


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


# --- SMA ---


class TestSMA:
    def test_is_alias_for_rolling_mean(self, df):
        sma = FUNCTIONS["sma"](df, df["close"], 3)
        rm = FUNCTIONS["rolling_mean"](df, df["close"], 3)
        pd.testing.assert_series_equal(sma, rm)

    def test_registered(self):
        assert "sma" in FUNCTIONS


# --- WMA ---


class TestWMA:
    def test_linear_weights(self, df):
        # WMA(3) on [103, 101, 103]: weights [1,2,3], sum=6
        # (103*1 + 101*2 + 103*3) / 6 = (103 + 202 + 309) / 6 = 614/6 = 102.333
        result = _wma(df, df["close"], 3)
        assert result.iloc[2] == pytest.approx(614.0 / 6, abs=0.01)

    def test_nan_warmup(self, df):
        result = _wma(df, df["close"], 3)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert not pd.isna(result.iloc[2])

    def test_heavier_on_recent(self):
        """WMA should weight recent values more than SMA."""
        # Uptrend: WMA > SMA because recent (higher) values get more weight
        col = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        df = pd.DataFrame({"close": col, "open": col, "high": col, "low": col, "volume": [100] * 5})
        wma = _wma(df, col, 3)
        sma = col.rolling(3).mean()
        # At bar 4: SMA = (3+4+5)/3 = 4.0, WMA = (3*1+4*2+5*3)/6 = 26/6 = 4.33
        assert wma.iloc[4] > sma.iloc[4]


# --- HMA ---


class TestHMA:
    def test_length(self, df):
        result = _hma(df, df["close"], 4)
        assert len(result) == len(df)

    def test_less_lag_than_sma(self):
        """HMA should react faster to price changes than SMA."""
        # Sharp trend change: flat then up
        col = pd.Series([100.0] * 20 + [100.0 + i * 2 for i in range(20)])
        df = pd.DataFrame(
            {"close": col, "open": col, "high": col, "low": col, "volume": [100] * 40}
        )
        hma = _hma(df, col, 9)
        sma = col.rolling(9).mean()
        # After trend starts, HMA should be closer to actual price (less lag)
        actual_price = col.iloc[-1]
        hma_lag = abs(actual_price - hma.iloc[-1])
        sma_lag = abs(actual_price - sma.iloc[-1])
        assert hma_lag < sma_lag

    def test_not_all_nan(self, df):
        result = _hma(df, df["close"], 4)
        assert result.notna().sum() > 0


# --- VWMA ---


class TestVWMA:
    def test_basic(self, df):
        result = _vwma(df, 3)
        assert len(result) == len(df)
        assert result.notna().sum() > 0

    def test_formula(self, df):
        # VWMA(3) = sum(close*volume, 3) / sum(volume, 3)
        cv = df["close"] * df["volume"]
        expected = cv.rolling(3).sum() / df["volume"].rolling(3).sum()
        result = _vwma(df, 3)
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_equal_volume_equals_sma(self):
        """When all volumes are equal, VWMA = SMA."""
        col = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        df = pd.DataFrame(
            {
                "close": col,
                "open": col,
                "high": col,
                "low": col,
                "volume": [100.0] * 5,
            }
        )
        vwma = _vwma(df, 3)
        sma = col.rolling(3).mean()
        pd.testing.assert_series_equal(vwma, sma, check_names=False)


# --- RMA ---


class TestRMA:
    def test_matches_wilder_smooth(self, df):
        from barb.functions._smoothing import wilder_smooth

        result = _rma(df, df["close"], 3)
        expected = wilder_smooth(df["close"], 3)
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_sma_seed(self):
        """First value should be SMA of first n values, not EMA."""
        col = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        df = pd.DataFrame({"close": col, "open": col, "high": col, "low": col, "volume": [100] * 5})
        result = _rma(df, col, 3)
        # SMA seed = (10+20+30)/3 = 20
        assert result.iloc[2] == pytest.approx(20.0)
        # Next: (1/3)*40 + (2/3)*20 = 26.67
        assert result.iloc[3] == pytest.approx(26.6667, abs=0.001)

    def test_differs_from_ema(self, df):
        """RMA (Wilder's) should differ from standard EMA."""
        rma = _rma(df, df["close"], 5)
        ema = df["close"].ewm(span=5, adjust=False).mean()
        # They use different alpha and seeding — should not be equal
        assert not np.allclose(rma.dropna().values, ema.iloc[4:].values)
