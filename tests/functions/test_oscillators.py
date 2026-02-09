"""Tests for oscillator functions."""

import numpy as np
import pandas as pd
import pytest

from barb.functions import FUNCTIONS


@pytest.fixture
def long_df():
    """30-bar DataFrame for indicator warmup tests."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    close = pd.Series(np.cumsum(np.random.randn(30)) + 100, index=dates)
    return pd.DataFrame(
        {
            "open": close.shift(1).bfill(),
            "high": close + np.random.rand(30) * 2,
            "low": close - np.random.rand(30) * 2,
            "close": close,
            "volume": np.random.randint(500, 2000, 30).astype(float),
        },
        index=dates,
    )


class TestRSI:
    def test_nan_warmup(self, long_df):
        """RSI(14) produces first value at bar n-1 (0-indexed)."""
        result = FUNCTIONS["rsi"](long_df, long_df["close"], 14)
        # .where(delta > 0, 0.0) converts diff's leading NaN to 0,
        # so gain/loss are fully non-NaN. wilder_smooth(14) seeds at
        # bar 13 (14th value, 0-indexed). Bars 0..12 = NaN.
        first_valid = result.first_valid_index()
        nan_count = result.index.get_loc(first_valid)
        assert nan_count == 13
        assert not result.loc[first_valid:].isna().any()

    def test_range_0_100(self, long_df):
        """RSI values must be between 0 and 100."""
        result = FUNCTIONS["rsi"](long_df, long_df["close"], 14)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_all_gains_rsi_100(self):
        """Monotonically increasing prices → RSI = 100."""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        close = pd.Series(range(100, 120), index=dates, dtype=float)
        df = pd.DataFrame({"close": close}, index=dates)
        result = FUNCTIONS["rsi"](df, df["close"], 5)
        valid = result.dropna()
        assert (valid == 100.0).all()

    def test_all_losses_rsi_0(self):
        """Monotonically decreasing prices → RSI = 0."""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        close = pd.Series(range(120, 100, -1), index=dates, dtype=float)
        df = pd.DataFrame({"close": close}, index=dates)
        result = FUNCTIONS["rsi"](df, df["close"], 5)
        valid = result.dropna()
        assert (valid == 0.0).all()

    def test_custom_period(self, long_df):
        """RSI with non-default period."""
        r5 = FUNCTIONS["rsi"](long_df, long_df["close"], 5)
        r14 = FUNCTIONS["rsi"](long_df, long_df["close"], 14)
        # Shorter period = more responsive = different values
        assert not r5.dropna().equals(r14.dropna())

    def test_preserves_index(self, long_df):
        result = FUNCTIONS["rsi"](long_df, long_df["close"], 14)
        assert list(result.index) == list(long_df.index)


class TestStochastic:
    def test_stoch_k_range(self, long_df):
        """Stochastic %K must be between 0 and 100."""
        result = FUNCTIONS["stoch_k"](long_df, 14)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_stoch_k_nan_warmup(self, long_df):
        """First n-1 bars should be NaN."""
        result = FUNCTIONS["stoch_k"](long_df, 14)
        assert result.iloc[:13].isna().all()
        assert not pd.isna(result.iloc[13])

    def test_stoch_k_at_high(self):
        """When close equals highest high, %K = 100."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "high": [10, 12, 15, 14, 15],
                "low": [8, 9, 10, 11, 12],
                "close": [9, 11, 15, 13, 15],  # last close = highest high
            },
            index=dates,
            dtype=float,
        )
        result = FUNCTIONS["stoch_k"](df, 3)
        # bar 4: close=15, highest(3)=15, lowest(3)=11 → (15-11)/(15-11)*100=100
        assert result.iloc[4] == 100.0

    def test_stoch_k_at_low(self):
        """When close equals lowest low, %K = 0."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "high": [10, 12, 15, 14, 13],
                "low": [8, 9, 10, 11, 8],
                "close": [9, 11, 14, 13, 8],  # last close = lowest low
            },
            index=dates,
            dtype=float,
        )
        result = FUNCTIONS["stoch_k"](df, 3)
        # bar 4: close=8, highest(3)=15, lowest(3)=8 → (8-8)/(15-8)*100=0
        assert result.iloc[4] == 0.0

    def test_stoch_d_is_sma_of_k(self, long_df):
        """%D = SMA(%K, smooth)."""
        k = FUNCTIONS["stoch_k"](long_df, 14)
        d = FUNCTIONS["stoch_d"](long_df, 14, 3)
        # At any point where d is valid, it should equal rolling mean of k
        k_sma = k.rolling(3).mean()
        valid = d.dropna()
        pd.testing.assert_series_equal(valid, k_sma.loc[valid.index])


class TestCCI:
    def test_nan_warmup(self, long_df):
        result = FUNCTIONS["cci"](long_df, 20)
        assert result.iloc[:19].isna().all()
        assert not pd.isna(result.iloc[19])

    def test_uses_mean_deviation(self):
        """CCI must use mean deviation, not std deviation."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "high": [12, 14, 13, 15, 14],
                "low": [8, 10, 9, 11, 10],
                "close": [10, 12, 11, 13, 12],
            },
            index=dates,
            dtype=float,
        )
        result = FUNCTIONS["cci"](df, 3)
        # Manual: TP = (H+L+C)/3
        # bar 2: TP = [10, 12, 11] → SMA=11, mean_dev = mean(|10-11|,|12-11|,|11-11|) = 2/3
        # CCI = (11 - 11) / (0.015 * 2/3) = 0
        assert abs(result.iloc[2]) < 0.01


class TestWilliamsR:
    def test_range(self, long_df):
        """Williams %R must be between -100 and 0."""
        result = FUNCTIONS["williams_r"](long_df, 14)
        valid = result.dropna()
        assert (valid >= -100).all()
        assert (valid <= 0).all()

    def test_at_high_is_zero(self):
        """When close = highest high, Williams %R = 0."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "high": [10, 12, 15, 14, 15],
                "low": [8, 9, 10, 11, 12],
                "close": [9, 11, 15, 13, 15],
            },
            index=dates,
            dtype=float,
        )
        result = FUNCTIONS["williams_r"](df, 3)
        assert result.iloc[4] == 0.0

    def test_at_low_is_minus_100(self):
        """When close = lowest low, Williams %R = -100."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "high": [10, 12, 15, 14, 13],
                "low": [8, 9, 10, 11, 8],
                "close": [9, 11, 14, 13, 8],
            },
            index=dates,
            dtype=float,
        )
        result = FUNCTIONS["williams_r"](df, 3)
        assert result.iloc[4] == -100.0


class TestMFI:
    def test_range(self, long_df):
        """MFI must be between 0 and 100."""
        result = FUNCTIONS["mfi"](long_df, 14)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_nan_warmup(self, long_df):
        result = FUNCTIONS["mfi"](long_df, 14)
        # diff() + .where converts leading NaN to 0, rolling(14) starts at bar 13
        assert result.iloc[:13].isna().all()
        assert not pd.isna(result.iloc[13])


class TestROC:
    def test_basic(self, long_df):
        result = FUNCTIONS["roc"](long_df, long_df["close"], 1)
        # roc = (close - prev_close) / prev_close * 100
        c0, c1 = long_df["close"].iloc[0], long_df["close"].iloc[1]
        expected = (c1 - c0) / c0 * 100
        assert abs(result.iloc[1] - expected) < 0.001

    def test_nan_first(self, long_df):
        result = FUNCTIONS["roc"](long_df, long_df["close"], 1)
        assert pd.isna(result.iloc[0])


class TestMomentum:
    def test_basic(self, long_df):
        result = FUNCTIONS["momentum"](long_df, long_df["close"], 1)
        expected = long_df["close"].iloc[1] - long_df["close"].iloc[0]
        assert abs(result.iloc[1] - expected) < 0.001

    def test_nan_warmup(self, long_df):
        result = FUNCTIONS["momentum"](long_df, long_df["close"], 10)
        assert result.iloc[:10].isna().all()
        assert not pd.isna(result.iloc[10])
