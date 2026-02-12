"""Golden reference tests: our indicators vs TradingView on AAPL.

Source: AAPL 1D, unadjusted, 2026-01-26 to 2026-02-09 (11 bars).
Price data: Yahoo Finance 530 bars (close matches FirstRateData exactly).
Reference: TradingView Barb Ref indicator (ADJ mode, scripts/tv_reference_table.pine).
Stock data = no contract rolls → exact match expected.

25 indicators × 11 bars = 275 data points verified.
"""

import csv
from pathlib import Path

import pandas as pd
import pytest

GOLDEN_DIR = Path(__file__).parent
YAHOO_CSV = GOLDEN_DIR / "AAPL_yahoo_1day.csv"
REF_CSV = GOLDEN_DIR / "AAPL_1day.csv"

TV_DATES = [
    "2026-01-26",
    "2026-01-27",
    "2026-01-28",
    "2026-01-29",
    "2026-01-30",
    "2026-02-02",
    "2026-02-03",
    "2026-02-04",
    "2026-02-05",
    "2026-02-06",
    "2026-02-09",
]


@pytest.fixture(scope="module")
def df():
    """Load Yahoo AAPL daily data (530 bars for indicator warmup)."""
    return pd.read_csv(YAHOO_CSV, parse_dates=["timestamp"], index_col="timestamp")


@pytest.fixture(scope="module")
def tv():
    """Parse TradingView reference values from AAPL_1day.csv."""
    lines = REF_CSV.read_text().splitlines()

    # Find TV section header
    tv_start = None
    for i, line in enumerate(lines):
        if line.startswith("## Source: TradingView"):
            tv_start = i
            break
    assert tv_start is not None

    # Parse CSV rows after header
    header = None
    rows = []
    for line in lines[tv_start:]:
        if line.startswith("##"):
            continue
        if header is None:
            header = line.split(",")
            continue
        if line.strip():
            rows.append(line)

    result = {}
    reader = csv.DictReader(rows, fieldnames=header)
    for row in reader:
        date = row["timestamp"]
        result[date] = {k: float(v) for k, v in row.items() if k != "timestamp"}
    return result


def _check(our_series, tv_ref, tv_col, dates, **approx_kw):
    """Assert our values match TV for each date."""
    for date in dates:
        ours = float(our_series.loc[date])
        expected = tv_ref[date][tv_col]
        assert ours == pytest.approx(expected, **approx_kw), (
            f"{tv_col} on {date}: ours={ours:.4f} vs TV={expected}"
        )


# --- Oscillators ---


class TestGoldenOscillators:
    def test_rsi(self, df, tv):
        from barb.functions.oscillators import _rsi

        _check(_rsi(df, df["close"], 14), tv, "RSI", TV_DATES, abs=0.5)

    def test_stoch_k(self, df, tv):
        from barb.functions.oscillators import _stoch_k

        _check(_stoch_k(df, 14), tv, "StochK", TV_DATES, abs=0.5)

    def test_williams_r(self, df, tv):
        from barb.functions.oscillators import _williams_r

        _check(_williams_r(df, 14), tv, "WilliamsR", TV_DATES, abs=0.5)

    def test_cci(self, df, tv):
        from barb.functions.oscillators import _cci

        _check(_cci(df, 20), tv, "CCI", TV_DATES, abs=1.0)

    def test_mfi(self, df, tv):
        from barb.functions.oscillators import _mfi

        # MFI uses volume which differs slightly between Yahoo and TV
        _check(_mfi(df, 14), tv, "MFI", TV_DATES, abs=1.0)


# --- Volatility ---


class TestGoldenVolatility:
    def test_tr(self, df, tv):
        from barb.functions.volatility import _tr

        _check(_tr(df), tv, "TR", TV_DATES, abs=0.01)

    def test_atr(self, df, tv):
        from barb.functions.volatility import _atr

        _check(_atr(df, 14), tv, "ATR", TV_DATES, abs=0.03)

    def test_natr(self, df, tv):
        from barb.functions.volatility import _natr

        _check(_natr(df, 14), tv, "NATR", TV_DATES, abs=0.02)

    def test_bbands_upper(self, df, tv):
        from barb.functions.volatility import _bbands_upper

        _check(_bbands_upper(df, df["close"], 20, 2.0), tv, "BB_Upper", TV_DATES, abs=0.1)

    def test_bbands_middle(self, df, tv):
        from barb.functions.volatility import _bbands_middle

        _check(_bbands_middle(df, df["close"], 20), tv, "BB_Middle", TV_DATES, abs=0.1)

    def test_bbands_lower(self, df, tv):
        from barb.functions.volatility import _bbands_lower

        _check(_bbands_lower(df, df["close"], 20, 2.0), tv, "BB_Lower", TV_DATES, abs=0.1)

    def test_bbands_width(self, df, tv):
        from barb.functions.volatility import _bbands_width

        _check(_bbands_width(df, df["close"], 20, 2.0), tv, "BB_Width", TV_DATES, abs=0.1)

    def test_bbands_pctb(self, df, tv):
        from barb.functions.volatility import _bbands_pctb

        _check(_bbands_pctb(df, df["close"], 20, 2.0), tv, "BB_PctB", TV_DATES, abs=0.005)

    def test_kc_upper(self, df, tv):
        from barb.functions.volatility import _kc_upper

        _check(_kc_upper(df, 20, 10, 1.5), tv, "KC_Upper", TV_DATES, abs=0.1)

    def test_kc_middle(self, df, tv):
        from barb.functions.volatility import _kc_middle

        _check(_kc_middle(df, 20), tv, "KC_Middle", TV_DATES, abs=0.1)

    def test_kc_lower(self, df, tv):
        from barb.functions.volatility import _kc_lower

        _check(_kc_lower(df, 20, 10, 1.5), tv, "KC_Lower", TV_DATES, abs=0.1)

    def test_kc_width(self, df, tv):
        from barb.functions.volatility import _kc_width

        _check(_kc_width(df, 20, 10, 1.5), tv, "KC_Width", TV_DATES, abs=0.001)


# --- Trend ---


class TestGoldenTrend:
    def test_macd(self, df, tv):
        from barb.functions.trend import _macd

        _check(_macd(df, df["close"], 12, 26), tv, "MACD", TV_DATES, abs=0.05)

    def test_macd_signal(self, df, tv):
        from barb.functions.trend import _macd_signal

        _check(_macd_signal(df, df["close"], 12, 26, 9), tv, "MACD_Signal", TV_DATES, abs=0.05)

    def test_macd_hist(self, df, tv):
        from barb.functions.trend import _macd_hist

        _check(_macd_hist(df, df["close"], 12, 26, 9), tv, "MACD_Hist", TV_DATES, abs=0.05)

    def test_plus_di(self, df, tv):
        from barb.functions.trend import _plus_di

        _check(_plus_di(df, 14), tv, "Plus_DI", TV_DATES, abs=0.5)

    def test_minus_di(self, df, tv):
        from barb.functions.trend import _minus_di

        _check(_minus_di(df, 14), tv, "Minus_DI", TV_DATES, abs=0.5)

    def test_adx(self, df, tv):
        from barb.functions.trend import _adx

        _check(_adx(df, 14), tv, "ADX", TV_DATES, abs=0.5)

    def test_supertrend(self, df, tv):
        from barb.functions.trend import _supertrend

        _check(_supertrend(df, 10, 3.0), tv, "SuperTrend", TV_DATES, abs=0.1)

    def test_supertrend_dir(self, df, tv):
        """Our convention: 1=up, -1=down. TV: 1=down, -1=up."""
        from barb.functions.trend import _supertrend_dir

        result = _supertrend_dir(df, 10, 3.0)
        for date in TV_DATES:
            ours = float(result.loc[date])
            tv_val = tv[date]["SuperTrend_Dir"]
            assert ours == pytest.approx(-tv_val, abs=0.001), (
                f"SuperTrend_Dir on {date}: ours={ours} vs TV={tv_val} (negated)"
            )

    def test_sar(self, df, tv):
        from barb.functions.trend import _sar

        _check(_sar(df), tv, "SAR", TV_DATES, abs=0.5)
