"""Tests for volume functions: OBV, VWAP, A/D Line, volume helpers."""

import pandas as pd
import pytest

from barb.functions.volume import _ad_line, _obv, _volume_ratio, _volume_sma, _vwap_day


@pytest.fixture(scope="module")
def df():
    from barb.data import load_data

    return load_data("NQ", "1d")


# --- OBV ---


class TestOBV:
    def test_length(self, df):
        result = _obv(df)
        assert len(result) == len(df)

    def test_direction(self):
        data = pd.DataFrame(
            {
                "open": [100, 101, 99, 102, 100],
                "high": [102, 103, 101, 104, 102],
                "low": [98, 99, 97, 100, 98],
                "close": [100, 102, 98, 103, 101],
                "volume": [1000, 1500, 1200, 1800, 900],
            }
        )
        result = _obv(data)
        # Bar 0: direction=0, OBV=0
        assert result.iloc[0] == 0
        # Bar 1: close up (102>100), OBV = 0 + 1500 = 1500
        assert result.iloc[1] == 1500
        # Bar 2: close down (98<102), OBV = 1500 - 1200 = 300
        assert result.iloc[2] == 300

    def test_flat_close_zero_contribution(self):
        data = pd.DataFrame(
            {
                "open": [100, 100],
                "high": [102, 102],
                "low": [98, 98],
                "close": [100, 100],
                "volume": [1000, 1500],
            }
        )
        result = _obv(data)
        # No change in close → volume * 0 = 0
        assert result.iloc[1] == 0


# --- VWAP ---


class TestVWAPDay:
    def test_length(self, df):
        result = _vwap_day(df)
        assert len(result) == len(df)

    def test_daily_trivial(self):
        """On daily data, VWAP = typical price (one bar per day)."""
        idx = pd.DatetimeIndex(["2024-01-02", "2024-01-03", "2024-01-04"])
        data = pd.DataFrame(
            {
                "open": [100, 110, 120],
                "high": [105, 115, 125],
                "low": [95, 105, 115],
                "close": [102, 112, 122],
                "volume": [1000, 1500, 1200],
            },
            index=idx,
        )
        result = _vwap_day(data)
        tp = (data["high"] + data["low"] + data["close"]) / 3
        pd.testing.assert_series_equal(result, tp, check_names=False)

    def test_intraday_reset(self):
        """VWAP resets at each new day."""
        idx = pd.DatetimeIndex(
            [
                "2024-01-02 09:30",
                "2024-01-02 09:31",
                "2024-01-03 09:30",
                "2024-01-03 09:31",
            ]
        )
        data = pd.DataFrame(
            {
                "open": [100, 101, 200, 201],
                "high": [102, 103, 202, 203],
                "low": [98, 99, 198, 199],
                "close": [101, 102, 201, 202],
                "volume": [1000, 2000, 1000, 2000],
            },
            index=idx,
        )
        result = _vwap_day(data)
        # Day 2 should reset — first bar of day 2 = typical price of that bar
        tp_day2_bar0 = (202 + 198 + 201) / 3
        assert result.iloc[2] == pytest.approx(tp_day2_bar0)


# --- A/D Line ---


class TestADLine:
    def test_length(self, df):
        result = _ad_line(df)
        assert len(result) == len(df)

    def test_formula(self):
        data = pd.DataFrame(
            {
                "open": [100, 100],
                "high": [110, 110],
                "low": [90, 90],
                "close": [105, 95],
                "volume": [1000, 1000],
            }
        )
        result = _ad_line(data)
        # Bar 0: CLV = ((105-90) - (110-105)) / (110-90) = (15-5)/20 = 0.5
        # AD = 0.5 * 1000 = 500
        assert result.iloc[0] == pytest.approx(500.0)
        # Bar 1: CLV = ((95-90) - (110-95)) / (110-90) = (5-15)/20 = -0.5
        # AD = 500 + (-0.5 * 1000) = 0
        assert result.iloc[1] == pytest.approx(0.0)

    def test_zero_range_bar(self):
        """When high == low, CLV should be 0 (no division error)."""
        data = pd.DataFrame(
            {
                "open": [100, 100],
                "high": [100, 100],
                "low": [100, 100],
                "close": [100, 100],
                "volume": [1000, 1000],
            }
        )
        result = _ad_line(data)
        assert result.iloc[0] == 0
        assert result.iloc[1] == 0


# --- Volume Ratio ---


class TestVolumeRatio:
    def test_formula(self, df):
        result = _volume_ratio(df, 20)
        expected = df["volume"] / df["volume"].rolling(20).mean()
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_above_one_means_above_average(self):
        vol = pd.Series([100] * 19 + [200])
        data = pd.DataFrame(
            {
                "open": vol,
                "high": vol,
                "low": vol,
                "close": vol,
                "volume": vol,
            }
        )
        result = _volume_ratio(data, 20)
        # Last bar volume (200) > SMA(20) of mixed → ratio > 1
        assert result.iloc[-1] > 1


# --- Volume SMA ---


class TestVolumeSMA:
    def test_formula(self, df):
        result = _volume_sma(df, 20)
        expected = df["volume"].rolling(20).mean()
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_nan_warmup(self, df):
        result = _volume_sma(df, 20)
        assert result.iloc[:19].isna().all()
        assert not pd.isna(result.iloc[19])
