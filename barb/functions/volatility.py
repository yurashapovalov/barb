"""Volatility functions: ATR, Bollinger Bands, Keltner Channel."""

import pandas as pd

from barb.functions._smoothing import wilder_smooth


def _tr(df):
    """True Range — max of (H-L, |H-prevC|, |L-prevC|)."""
    prev_close = df["close"].shift(1)
    hl = df["high"] - df["low"]
    hc = (df["high"] - prev_close).abs()
    lc = (df["low"] - prev_close).abs()
    return pd.concat([hl, hc, lc], axis=1).max(axis=1)


def _atr(df, n=14):
    """Average True Range — Wilder's smoothing of TR.

    Exact TradingView ta.atr() match.
    """
    return wilder_smooth(_tr(df), int(n))


def _natr(df, n=14):
    """Normalized ATR — ATR as percentage of close."""
    return _atr(df, n) / df["close"] * 100


# --- Bollinger Bands ---


def _bbands_upper(df, col, n=20, mult=2.0):
    """Bollinger upper band = SMA + mult * stdev."""
    n = int(n)
    sma = col.rolling(n).mean()
    # ddof=0: population std, matches TradingView
    std = col.rolling(n).std(ddof=0)
    return sma + float(mult) * std


def _bbands_middle(df, col, n=20):
    """Bollinger middle band = SMA."""
    return col.rolling(int(n)).mean()


def _bbands_lower(df, col, n=20, mult=2.0):
    """Bollinger lower band = SMA - mult * stdev."""
    n = int(n)
    sma = col.rolling(n).mean()
    std = col.rolling(n).std(ddof=0)
    return sma - float(mult) * std


def _bbands_width(df, col, n=20, mult=2.0):
    """Bollinger bandwidth = (upper - lower) / middle * 100. Matches TV ta.bbw()."""
    n = int(n)
    sma = col.rolling(n).mean()
    std = col.rolling(n).std(ddof=0)
    return (2 * float(mult) * std) / sma * 100


def _bbands_pctb(df, col, n=20, mult=2.0):
    """Bollinger %B — where price is between bands (0 = lower, 1 = upper)."""
    n = int(n)
    mult = float(mult)
    sma = col.rolling(n).mean()
    std = col.rolling(n).std(ddof=0)
    upper = sma + mult * std
    lower = sma - mult * std
    return (col - lower) / (upper - lower)


# --- Keltner Channel ---


def _kc_upper(df, n=20, atr_n=10, mult=1.5):
    """Keltner upper = EMA(close, n) + mult * ATR(atr_n)."""
    ema = df["close"].ewm(span=int(n), adjust=False).mean()
    return ema + float(mult) * _atr(df, int(atr_n))


def _kc_middle(df, n=20):
    """Keltner middle = EMA(close, n)."""
    return df["close"].ewm(span=int(n), adjust=False).mean()


def _kc_lower(df, n=20, atr_n=10, mult=1.5):
    """Keltner lower = EMA(close, n) - mult * ATR(atr_n)."""
    ema = df["close"].ewm(span=int(n), adjust=False).mean()
    return ema - float(mult) * _atr(df, int(atr_n))


def _kc_width(df, n=20, atr_n=10, mult=1.5):
    """Keltner width = (upper - lower) / middle."""
    ema = df["close"].ewm(span=int(n), adjust=False).mean()
    atr = _atr(df, int(atr_n))
    return (2 * float(mult) * atr) / ema


# --- Donchian Channel ---


def _donchian_upper(df, n=20):
    """Donchian upper = highest high over n bars."""
    return df["high"].rolling(int(n)).max()


def _donchian_lower(df, n=20):
    """Donchian lower = lowest low over n bars."""
    return df["low"].rolling(int(n)).min()


VOLATILITY_FUNCTIONS = {
    "tr": _tr,
    "atr": _atr,
    "natr": _natr,
    "bbands_upper": _bbands_upper,
    "bbands_middle": _bbands_middle,
    "bbands_lower": _bbands_lower,
    "bbands_width": _bbands_width,
    "bbands_pctb": _bbands_pctb,
    "kc_upper": _kc_upper,
    "kc_middle": _kc_middle,
    "kc_lower": _kc_lower,
    "kc_width": _kc_width,
    "donchian_upper": _donchian_upper,
    "donchian_lower": _donchian_lower,
}

VOLATILITY_SIGNATURES = {
    "tr": "tr()",
    "atr": "atr(n=14)",
    "natr": "natr(n=14)",
    "bbands_upper": "bbands_upper(col, n=20, mult=2.0)",
    "bbands_middle": "bbands_middle(col, n=20)",
    "bbands_lower": "bbands_lower(col, n=20, mult=2.0)",
    "bbands_width": "bbands_width(col, n=20, mult=2.0)",
    "bbands_pctb": "bbands_pctb(col, n=20, mult=2.0)",
    "kc_upper": "kc_upper(n=20, atr_n=10, mult=1.5)",
    "kc_middle": "kc_middle(n=20)",
    "kc_lower": "kc_lower(n=20, atr_n=10, mult=1.5)",
    "kc_width": "kc_width(n=20, atr_n=10, mult=1.5)",
    "donchian_upper": "donchian_upper(n=20)",
    "donchian_lower": "donchian_lower(n=20)",
}
