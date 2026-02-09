"""Tests for Wilder's smoothing (RMA)."""

import numpy as np
import pandas as pd
import pytest

from barb.functions._smoothing import wilder_smooth


@pytest.fixture
def series():
    """Simple 10-value series for smoothing tests."""
    return pd.Series(
        [44, 44, 44, 46, 43, 42, 44, 43, 44, 45],
        index=pd.date_range("2024-01-01", periods=10, freq="D"),
        dtype=float,
    )


class TestWilderSmooth:
    def test_nan_warmup(self, series):
        """First n-1 values must be NaN."""
        result = wilder_smooth(series, 5)
        for i in range(4):
            assert pd.isna(result.iloc[i])
        assert not pd.isna(result.iloc[4])

    def test_sma_seed(self, series):
        """First non-NaN value = SMA of first n values."""
        result = wilder_smooth(series, 5)
        # SMA of first 5: mean(44, 44, 44, 46, 43) = 44.2
        expected_seed = (44 + 44 + 44 + 46 + 43) / 5
        assert result.iloc[4] == pytest.approx(expected_seed)

    def test_recursion(self, series):
        """Values after seed follow rma[t] = α * val[t] + (1-α) * rma[t-1]."""
        result = wilder_smooth(series, 5)
        alpha = 1 / 5

        seed = (44 + 44 + 44 + 46 + 43) / 5  # 44.2
        # bar 5: val=42 → 0.2 * 42 + 0.8 * 44.2 = 8.4 + 35.36 = 43.76
        expected = alpha * 42 + (1 - alpha) * seed
        assert result.iloc[5] == pytest.approx(expected)

        # bar 6: val=44 → 0.2 * 44 + 0.8 * 43.76 = 8.8 + 35.008 = 43.808
        expected2 = alpha * 44 + (1 - alpha) * expected
        assert result.iloc[6] == pytest.approx(expected2)

    def test_differs_from_ewm(self, series):
        """Wilder's smooth must NOT equal pandas ewm — different seed."""
        wilder = wilder_smooth(series, 5)
        ewm = series.ewm(alpha=1 / 5, adjust=False).mean()

        # First non-NaN values differ because of SMA seed vs first-value seed
        # ewm starts from bar 0 with value 44
        # wilder starts from bar 4 with SMA = 44.2
        # After bar 4, all subsequent values differ
        assert wilder.iloc[4] != pytest.approx(ewm.iloc[4], abs=0.001)

    def test_preserves_index(self, series):
        result = wilder_smooth(series, 3)
        assert list(result.index) == list(series.index)
        assert len(result) == len(series)

    def test_n_equals_1(self, series):
        """With n=1, SMA seed = first value, α=1 → result = original series."""
        result = wilder_smooth(series, 1)
        # α=1: rma[t] = 1 * val[t] + 0 * rma[t-1] = val[t]
        pd.testing.assert_series_equal(result, series)

    def test_series_shorter_than_n(self):
        """When series has fewer values than n, return all NaN."""
        short = pd.Series([1.0, 2.0, 3.0], index=pd.date_range("2024-01-01", periods=3))
        result = wilder_smooth(short, 5)
        assert result.isna().all()

    def test_empty_series(self):
        """Empty series returns empty series."""
        empty = pd.Series([], dtype=float)
        result = wilder_smooth(empty, 5)
        assert len(result) == 0

    def test_series_with_leading_nans(self):
        """NaN at the start should be skipped — seed from first n non-NaN values."""
        s = pd.Series(
            [np.nan, np.nan, 10, 20, 30, 40],
            index=pd.date_range("2024-01-01", periods=6, freq="D"),
        )
        result = wilder_smooth(s, 3)
        # First 2 are NaN from data, bars 2-3 are NaN (warmup)
        # Seed at index 4: SMA(10, 20, 30) = 20
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[2])
        assert pd.isna(result.iloc[3])
        assert result.iloc[4] == pytest.approx(20.0)

        # bar 5: val=40 → (1/3)*40 + (2/3)*20 = 13.333 + 13.333 = 26.667
        alpha = 1 / 3
        expected = alpha * 40 + (1 - alpha) * 20
        assert result.iloc[5] == pytest.approx(expected)

    def test_nan_in_middle_carries_forward(self):
        """NaN in the middle of data carries previous result forward."""
        s = pd.Series(
            [10, 20, 30, np.nan, 50],
            index=pd.date_range("2024-01-01", periods=5, freq="D"),
        )
        result = wilder_smooth(s, 3)
        seed = 20.0  # SMA(10, 20, 30)
        # bar 3: NaN → carry forward seed
        assert result.iloc[3] == pytest.approx(seed)
        # bar 4: val=50 → (1/3)*50 + (2/3)*20 = 30
        alpha = 1 / 3
        expected = alpha * 50 + (1 - alpha) * seed
        assert result.iloc[4] == pytest.approx(expected)
