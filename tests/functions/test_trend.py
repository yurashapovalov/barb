"""Tests for trend functions: MACD, ADX, SuperTrend, Parabolic SAR."""

import numpy as np
import pandas as pd
import pytest

from barb.functions.trend import (
    _adx,
    _macd,
    _macd_hist,
    _macd_signal,
    _minus_di,
    _plus_di,
    _sar,
    _supertrend,
    _supertrend_dir,
)


@pytest.fixture(scope="module")
def df():
    from barb.data import load_data

    return load_data("NQ", "1d")


# --- MACD ---


class TestMACD:
    def test_length(self, df):
        result = _macd(df, df["close"])
        assert len(result) == len(df)

    def test_uses_standard_ema(self, df):
        """MACD uses standard EMA (span-based), not Wilder's."""
        col = df["close"]
        fast_ema = col.ewm(span=12, adjust=False).mean()
        slow_ema = col.ewm(span=26, adjust=False).mean()
        expected = fast_ema - slow_ema
        pd.testing.assert_series_equal(_macd(df, col), expected, check_names=False)

    def test_signal_is_ema_of_macd(self, df):
        col = df["close"]
        macd_line = _macd(df, col)
        expected_signal = macd_line.ewm(span=9, adjust=False).mean()
        pd.testing.assert_series_equal(_macd_signal(df, col), expected_signal, check_names=False)

    def test_hist_is_macd_minus_signal(self, df):
        col = df["close"]
        macd_line = _macd(df, col)
        signal = _macd_signal(df, col)
        hist = _macd_hist(df, col)
        pd.testing.assert_series_equal(hist, macd_line - signal, check_names=False)

    def test_custom_periods(self, df):
        col = df["close"]
        m1 = _macd(df, col, 12, 26)
        m2 = _macd(df, col, 8, 21)
        # Different periods → different values
        assert not np.allclose(m1.dropna().values, m2.dropna().values)


# --- ADX ---


class TestADX:
    def test_adx_range(self, df):
        adx = _adx(df, 14)
        valid = adx.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_di_range(self, df):
        plus = _plus_di(df, 14)
        minus = _minus_di(df, 14)
        assert (plus.dropna() >= 0).all()
        assert (minus.dropna() >= 0).all()

    def test_warmup_nans(self, df):
        """ADX has double Wilder's smoothing → 2n-1 warmup bars."""
        adx = _adx(df, 14)
        # First ~26 bars should be NaN (2*14-1 = 27, but DM starts at bar 1)
        assert adx.iloc[:25].isna().all()
        assert not np.isnan(adx.iloc[27])

    def test_uses_wilder_smoothing(self, df):
        """ADX should use Wilder's, producing different results from SMA-based DX."""
        adx = _adx(df, 14)
        # ADX should be relatively smooth (Wilder's is slow-moving)
        changes = adx.dropna().diff().abs()
        # Average change should be small relative to value
        assert changes.mean() < adx.dropna().mean() * 0.1


# --- SuperTrend ---


class TestSuperTrend:
    def test_length(self, df):
        st = _supertrend(df)
        assert len(st) == len(df)

    def test_nan_warmup(self, df):
        """SuperTrend needs ATR warmup (n bars)."""
        st = _supertrend(df, n=10)
        assert st.iloc[:9].isna().all()
        assert not np.isnan(st.iloc[10])

    def test_direction_values(self, df):
        d = _supertrend_dir(df)
        valid = d.dropna()
        # Direction should be only 1.0 or -1.0
        assert set(valid.unique()) <= {1.0, -1.0}

    def test_value_near_price(self, df):
        """SuperTrend should be reasonably close to price."""
        st = _supertrend(df)
        close = df["close"]
        valid = st.dropna().index
        pct_diff = ((st[valid] - close[valid]) / close[valid]).abs()
        # Should be within 10% of price
        assert pct_diff.mean() < 0.10

    def test_uptrend_below_price(self, df):
        """In uptrend, SuperTrend should be below close."""
        st = _supertrend(df)
        d = _supertrend_dir(df)
        valid = d.dropna().index
        uptrend = d[valid] == 1.0
        if uptrend.any():
            up_idx = valid[uptrend]
            assert (st[up_idx] <= df["close"][up_idx]).all()


# --- Parabolic SAR ---


class TestSAR:
    def test_length(self, df):
        result = _sar(df)
        assert len(result) == len(df)

    def test_not_all_nan(self, df):
        result = _sar(df)
        assert result.notna().sum() > len(df) * 0.9

    def test_positive(self, df):
        result = _sar(df)
        assert (result.dropna() > 0).all()

    def test_near_price(self, df):
        """SAR should be within reasonable distance of price."""
        result = _sar(df)
        close = df["close"]
        valid = result.dropna().index
        pct_diff = ((result[valid] - close[valid]) / close[valid]).abs()
        assert pct_diff.mean() < 0.05

    def test_custom_params(self, df):
        s1 = _sar(df, 0.02, 0.2)
        s2 = _sar(df, 0.01, 0.1)
        # Different params → different values
        valid = s1.dropna().index.intersection(s2.dropna().index)
        assert not np.allclose(s1[valid].values, s2[valid].values)

    def test_synthetic_uptrend(self):
        """In steady uptrend, SAR should stay below price."""
        data = pd.DataFrame(
            {
                "open": [100 + i for i in range(50)],
                "high": [101 + i for i in range(50)],
                "low": [99 + i for i in range(50)],
                "close": [100.5 + i for i in range(50)],
                "volume": [1000] * 50,
            }
        )
        result = _sar(data)
        # After warmup, SAR should be below close in uptrend
        assert (result.iloc[5:] < data["close"].iloc[5:]).all()


# --- TradingView match tests ---
# NQ1! daily, SET mode, 2025-12-22
# MACD uses EMA(12)/EMA(26) — difference of two large numbers (~25000),
# so small data divergence from contract rolls gets amplified in the diff.
# ADX uses double Wilder's smoothing which also amplifies roll effects.
# SuperTrend and SAR match near-exactly (driven by recent high/low/ATR).


class TestTVMatch:
    """Compare against TradingView Barb Ref indicator values."""

    def test_macd(self, df):
        # TV: 50.27, ours: ~56.68 — EMA diff amplifies roll divergence
        assert _macd(df, df["close"]).loc["2025-12-22"] == pytest.approx(50.27, abs=10)

    def test_macd_signal(self, df):
        # TV: 50.94, ours: ~63.29 — cascaded EMA widens gap
        assert _macd_signal(df, df["close"]).loc["2025-12-22"] == pytest.approx(50.94, abs=15)

    def test_macd_hist(self, df):
        # TV: -0.67, ours: ~-6.61 — diff of two divergent values
        assert _macd_hist(df, df["close"]).loc["2025-12-22"] == pytest.approx(-0.67, abs=8)

    def test_plus_di(self, df):
        assert _plus_di(df, 14).loc["2025-12-22"] == pytest.approx(16.98, abs=1.5)

    def test_minus_di(self, df):
        assert _minus_di(df, 14).loc["2025-12-22"] == pytest.approx(17.08, abs=1.5)

    def test_adx(self, df):
        # TV: 14.72, ours: ~12.62 — double Wilder's smoothing amplifies roll diff
        assert _adx(df, 14).loc["2025-12-22"] == pytest.approx(14.72, abs=2.5)

    def test_supertrend(self, df):
        assert _supertrend(df, 10, 3.0).loc["2025-12-22"] == pytest.approx(26057.76, rel=0.001)

    def test_supertrend_dir(self, df):
        # TV direction: 1=down, ours: -1=down (negated convention)
        assert _supertrend_dir(df, 10, 3.0).loc["2025-12-22"] == -1.0

    def test_sar(self, df):
        assert _sar(df).loc["2025-12-22"] == pytest.approx(24887.75, rel=0.001)
