"""Tests for volatility functions: ATR, Bollinger Bands, Keltner Channel."""

import numpy as np
import pandas as pd
import pytest

from barb.functions.volatility import (
    _atr,
    _bbands_lower,
    _bbands_middle,
    _bbands_pctb,
    _bbands_upper,
    _bbands_width,
    _kc_lower,
    _kc_middle,
    _kc_upper,
    _kc_width,
    _natr,
    _tr,
)


@pytest.fixture(scope="module")
def df():
    from barb.data import load_data

    return load_data("NQ", "1d")


# --- True Range ---


class TestTR:
    def test_basic(self, df):
        tr = _tr(df)
        assert len(tr) == len(df)
        # TR is always positive (except first bar which is NaN-ish)
        assert (tr.dropna() >= 0).all()

    def test_first_bar_is_high_minus_low(self, df):
        # First bar has no prev close, so TR = H - L
        tr = _tr(df)
        expected = df["high"].iloc[0] - df["low"].iloc[0]
        # First bar: prev_close is NaN, so max(H-L, NaN, NaN) = H-L
        assert tr.iloc[0] == pytest.approx(expected)

    def test_gap_up(self):
        # When gap up: |H - prevC| > H - L
        data = pd.DataFrame(
            {
                "open": [100, 110],
                "high": [105, 112],
                "low": [95, 109],
                "close": [102, 111],
                "volume": [100, 100],
            }
        )
        tr = _tr(data)
        # Bar 1: H-L=3, |H-prevC|=|112-102|=10, |L-prevC|=|109-102|=7
        assert tr.iloc[1] == pytest.approx(10.0)


# --- ATR ---


class TestATR:
    def test_length(self, df):
        atr = _atr(df, 14)
        assert len(atr) == len(df)

    def test_positive(self, df):
        atr = _atr(df, 14)
        assert (atr.dropna() > 0).all()

    def test_nan_first_n(self, df):
        atr = _atr(df, 14)
        # First 14 bars should have NaN (13 TR NaN-like + seed at 14)
        assert atr.iloc[:13].isna().all()
        assert not np.isnan(atr.iloc[14])

    def test_uses_wilder_smoothing(self, df):
        """ATR should use Wilder's smoothing, not SMA."""
        atr = _atr(df, 14)
        tr = _tr(df)
        sma_atr = tr.rolling(14).mean()
        # After warmup, Wilder's and SMA diverge
        diff = abs(atr.iloc[100] - sma_atr.iloc[100])
        assert diff > 1  # They should be meaningfully different


# --- NATR ---


class TestNATR:
    def test_is_percentage(self, df):
        natr = _natr(df, 14)
        # NATR should be reasonable percentage (0.5% - 10% for NQ)
        last = natr.dropna().iloc[-1]
        assert 0.1 < last < 20


# --- Bollinger Bands ---


class TestBollingerBands:
    def test_upper_above_middle_above_lower(self, df):
        close = df["close"]
        upper = _bbands_upper(df, close)
        middle = _bbands_middle(df, close)
        lower = _bbands_lower(df, close)
        valid = upper.dropna().index
        assert (upper[valid] >= middle[valid]).all()
        assert (middle[valid] >= lower[valid]).all()

    def test_middle_is_sma(self, df):
        close = df["close"]
        middle = _bbands_middle(df, close, 20)
        sma = close.rolling(20).mean()
        pd.testing.assert_series_equal(middle, sma, check_names=False)

    def test_ddof_zero(self, df):
        """Bollinger uses population std (ddof=0), not sample std (ddof=1)."""
        close = df["close"]
        upper = _bbands_upper(df, close, 20, 2.0)
        middle = _bbands_middle(df, close, 20)
        # Compute with ddof=1 (wrong) and ddof=0 (correct)
        std_pop = close.rolling(20).std(ddof=0)
        std_sample = close.rolling(20).std(ddof=1)
        upper_pop = middle + 2.0 * std_pop
        upper_sample = middle + 2.0 * std_sample
        # Our implementation should match ddof=0
        pd.testing.assert_series_equal(upper, upper_pop, check_names=False)
        # And differ from ddof=1
        assert not np.allclose(upper.dropna().values, upper_sample.dropna().values)

    def test_width(self, df):
        close = df["close"]
        width = _bbands_width(df, close)
        assert (width.dropna() >= 0).all()

    def test_pctb_range(self, df):
        close = df["close"]
        pctb = _bbands_pctb(df, close)
        # %B can go outside 0-1 but should mostly be in range
        valid = pctb.dropna()
        in_range = ((valid >= -0.5) & (valid <= 1.5)).mean()
        assert in_range > 0.95

    def test_custom_mult(self, df):
        close = df["close"]
        upper_2 = _bbands_upper(df, close, 20, 2.0)
        upper_3 = _bbands_upper(df, close, 20, 3.0)
        valid = upper_2.dropna().index
        assert (upper_3[valid] > upper_2[valid]).all()


# --- Keltner Channel ---


class TestKeltnerChannel:
    def test_upper_above_lower(self, df):
        upper = _kc_upper(df)
        lower = _kc_lower(df)
        valid = upper.dropna().index.intersection(lower.dropna().index)
        assert (upper[valid] >= lower[valid]).all()

    def test_middle_is_ema(self, df):
        middle = _kc_middle(df, 20)
        ema = df["close"].ewm(span=20, adjust=False).mean()
        pd.testing.assert_series_equal(middle, ema, check_names=False)

    def test_width_positive(self, df):
        width = _kc_width(df)
        assert (width.dropna() > 0).all()

    def test_uses_atr(self, df):
        """Keltner should use ATR, not std dev."""
        upper = _kc_upper(df, 20, 10, 1.5)
        middle = _kc_middle(df, 20)
        atr = _atr(df, 10)
        expected_upper = middle + 1.5 * atr
        valid = expected_upper.dropna().index
        pd.testing.assert_series_equal(upper[valid], expected_upper[valid], check_names=False)


# --- TradingView match tests ---
# NQ1! daily, SET mode, 2025-12-22
# Tolerances account for contract roll divergence (~4 bars/quarter).
# TR is single-bar so exact. ATR/BB/KC use lookback windows that may
# cross roll dates, causing small divergence via smoothing memory.


class TestTVMatch:
    """Compare against TradingView Barb Ref indicator values."""

    def test_tr(self, df):
        assert _tr(df).loc["2025-12-22"] == pytest.approx(220.00, abs=0.5)

    def test_atr(self, df):
        # TV: 426.17, ours: 426.61 — Wilder's smoothing amplifies roll diff
        assert _atr(df, 14).loc["2025-12-22"] == pytest.approx(426.17, rel=0.005)

    def test_natr(self, df):
        assert _natr(df, 14).loc["2025-12-22"] == pytest.approx(1.66, abs=0.02)

    def test_bbands_middle(self, df):
        # TV: 25440.86 — SMA(20) captures roll bars in window
        col = df["close"]
        assert _bbands_middle(df, col, 20).loc["2025-12-22"] == pytest.approx(25440.86, rel=0.002)

    def test_bbands_upper(self, df):
        col = df["close"]
        assert _bbands_upper(df, col, 20, 2.0).loc["2025-12-22"] == pytest.approx(
            25986.09, rel=0.002
        )

    def test_bbands_lower(self, df):
        col = df["close"]
        assert _bbands_lower(df, col, 20, 2.0).loc["2025-12-22"] == pytest.approx(
            24895.64, rel=0.003
        )

    def test_bbands_pctb(self, df):
        col = df["close"]
        assert _bbands_pctb(df, col, 20, 2.0).loc["2025-12-22"] == pytest.approx(0.73, abs=0.02)

    def test_kc_middle(self, df):
        # TV: 25392.02 — EMA(20) has longer memory than SMA
        assert _kc_middle(df, 20).loc["2025-12-22"] == pytest.approx(25392.02, rel=0.002)

    def test_kc_upper(self, df):
        assert _kc_upper(df, 20, 10, 1.5).loc["2025-12-22"] == pytest.approx(26017.86, rel=0.002)

    def test_kc_lower(self, df):
        assert _kc_lower(df, 20, 10, 1.5).loc["2025-12-22"] == pytest.approx(24766.18, rel=0.002)
