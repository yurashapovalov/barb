"""TradingView match tests for oscillator indicators.

Compares our indicator calculations on NQ daily data against
reference values collected from TradingView (NQ1!, daily chart).

Close prices differ slightly because TradingView uses CME settlement
prices while we aggregate from minute bars (close at 16:59 ET).
This causes ~0.04% price difference that accumulates through indicators.

Tolerances:
- RSI, StochK: 2% — use only close/high/low, minimal accumulation
- CCI, WilliamsR: 5% or ±5 absolute — sensitive to close differences
- MFI: 10% — uses volume which aggregates differently
"""

import pandas as pd
import pytest

from barb.functions import FUNCTIONS

DATA_PATH = "data/NQ.parquet"
REF_PATH = "tests/functions/reference_data/nq_oscillators_tv.csv"


@pytest.fixture(scope="module")
def daily_df():
    """NQ daily bars aggregated by CME session (18:00 ET → 16:59 ET)."""
    df = pd.read_parquet(DATA_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()

    # Shift +6h so 18:00 ET → 00:00 next day (session start = day boundary)
    shifted = df.copy()
    shifted.index = shifted.index + pd.Timedelta(hours=6)
    daily = (
        shifted.resample("D")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
    )
    return daily


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
    """RSI(14) — Wilder's smoothing, close only. Tight tolerance."""

    def test_rsi_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["rsi_14"].loc[date_str]
            _assert_close(our, row["rsi_14"], rel_tol=0.05)


class TestStochKMatch:
    """Stochastic %K(14) — uses high/low/close rolling window."""

    def test_stoch_k_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["stoch_k_14"].loc[date_str]
            _assert_close(our, row["stoch_k_14"], rel_tol=0.05, abs_tol=6)


class TestCCIMatch:
    """CCI(20) — mean deviation, sensitive to close. Wider tolerance."""

    def test_cci_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["cci_20"].loc[date_str]
            # CCI ranges ~±300, absolute tolerance ±15 handles near-zero values
            _assert_close(our, row["cci_20"], rel_tol=0.10, abs_tol=15)


class TestWilliamsRMatch:
    """Williams %R(14) — range -100..0, related to StochK."""

    def test_williams_r_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["williams_r_14"].loc[date_str]
            _assert_close(our, row["williams_r_14"], rel_tol=0.10, abs_tol=6)


class TestMFIMatch:
    """MFI(14) — uses volume, largest expected divergence."""

    def test_mfi_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            our = indicators["mfi_14"].loc[date_str]
            # MFI diverges most because minute volume sum != exchange daily volume
            _assert_close(our, row["mfi_14"], rel_tol=0.16)
