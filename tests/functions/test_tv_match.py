"""TradingView match tests for oscillator indicators.

Compares our indicator calculations on NQ 1d (settlement) data against
reference values collected from TradingView (NQ1!, daily chart).

Reference dates are chosen away from contract rolls (mid-quarter)
where our data provider and TradingView agree on OHLCV.

RSI uses Wilder's smoothing (exponential), so contract roll differences
propagate through history causing ~0.5% divergence. Window-based
indicators (CCI, StochK, WilliamsR, MFI) match exactly when the
lookback window contains no roll bars.
"""

import pandas as pd
import pytest

from barb.data import load_data
from barb.functions import FUNCTIONS

REF_PATH = "tests/functions/reference_data/nq_oscillators_tv.csv"


@pytest.fixture(scope="module")
def daily_df():
    """NQ daily bars (settlement close, matches TradingView)."""
    return load_data("NQ", "1d")


@pytest.fixture(scope="module")
def ref_data():
    """TradingView reference values."""
    return pd.read_csv(REF_PATH, parse_dates=["date"], index_col="date")


@pytest.fixture(scope="module")
def indicators(daily_df):
    """Pre-compute all indicators once."""
    return {
        "rsi_14": FUNCTIONS["rsi"](daily_df, daily_df["close"], 14),
        "cci_20": FUNCTIONS["cci"](daily_df, 20),
        "stoch_k_14": FUNCTIONS["stoch_k"](daily_df, 14),
        "williams_r_14": FUNCTIONS["williams_r"](daily_df, 14),
        "mfi_14": FUNCTIONS["mfi"](daily_df, 14),
    }


def _assert_close(our_val, tv_val, rel_tol, abs_tol=0):
    """Assert values match within relative OR absolute tolerance."""
    diff = abs(our_val - tv_val)
    if abs_tol and diff <= abs_tol:
        return
    if tv_val == 0:
        assert diff <= abs_tol, f"ours={our_val:.2f} tv={tv_val:.2f} diff={diff:.2f}"
        return
    pct = diff / abs(tv_val)
    assert pct <= rel_tol, f"ours={our_val:.2f} tv={tv_val:.2f} diff={pct:.1%} > {rel_tol:.0%}"


class TestRSIMatch:
    """RSI(14) — Wilder's smoothing, exponential history. Roll propagates."""

    def test_rsi_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["rsi_14"].loc[date_str]
            _assert_close(our, row["rsi_14"], rel_tol=0.01, abs_tol=0.5)


class TestStochKMatch:
    """Stochastic %K(14) — 14-bar window, no history dependence."""

    def test_stoch_k_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["stoch_k_14"].loc[date_str]
            _assert_close(our, row["stoch_k_14"], rel_tol=0.01, abs_tol=0.5)


class TestCCIMatch:
    """CCI(20) — 20-bar window, no history dependence."""

    def test_cci_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["cci_20"].loc[date_str]
            _assert_close(our, row["cci_20"], rel_tol=0.01, abs_tol=0.5)


class TestWilliamsRMatch:
    """Williams %R(14) — 14-bar window, no history dependence."""

    def test_williams_r_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["williams_r_14"].loc[date_str]
            _assert_close(our, row["williams_r_14"], rel_tol=0.01, abs_tol=0.5)


class TestMFIMatch:
    """MFI(14) — 14-bar window, uses volume."""

    def test_mfi_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["mfi_14"].loc[date_str]
            _assert_close(our, row["mfi_14"], rel_tol=0.01, abs_tol=0.5)
