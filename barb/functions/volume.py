"""Volume functions: OBV, VWAP, A/D Line, volume helpers."""

import numpy as np


def _obv(df):
    """On Balance Volume — cumulative volume in direction of close change."""
    direction = np.sign(df["close"].diff())
    # First bar: no direction, treat as 0
    direction.iloc[0] = 0
    return (df["volume"] * direction).cumsum()


def _vwap_day(df):
    """VWAP with daily reset — typical price * volume / cumulative volume per day.

    Resets accumulation at the start of each calendar day.
    On daily data, VWAP = typical price (trivially).
    """
    tp = (df["high"] + df["low"] + df["close"]) / 3
    tpv = tp * df["volume"]

    # Group by date for reset
    dates = df.index.date
    cum_tpv = tpv.groupby(dates).cumsum()
    cum_vol = df["volume"].groupby(dates).cumsum()
    return cum_tpv / cum_vol


def _ad_line(df):
    """Accumulation/Distribution Line.

    CLV = ((Close-Low) - (High-Close)) / (High-Low)
    High == Low → CLV = 0 (zero-range bars).
    """
    high_low = df["high"] - df["low"]
    clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / high_low
    clv = clv.fillna(0)  # zero-range bars
    return (clv * df["volume"]).cumsum()


def _volume_ratio(df, n=20):
    """Volume ratio — current volume / SMA(volume, n)."""
    n = int(n)
    return df["volume"] / df["volume"].rolling(n).mean()


def _volume_sma(df, n=20):
    """Simple moving average of volume."""
    return df["volume"].rolling(int(n)).mean()


VOLUME_FUNCTIONS = {
    "obv": _obv,
    "vwap_day": _vwap_day,
    "ad_line": _ad_line,
    "volume_ratio": _volume_ratio,
    "volume_sma": _volume_sma,
}

VOLUME_SIGNATURES = {
    "obv": "obv()",
    "vwap_day": "vwap_day()",
    "ad_line": "ad_line()",
    "volume_ratio": "volume_ratio(n=20)",
    "volume_sma": "volume_sma(n=20)",
}

VOLUME_DESCRIPTIONS = {
    "obv": "On Balance Volume — cumulative volume in direction of price change",
    "vwap_day": "VWAP with daily reset — volume-weighted average price",
    "ad_line": "Accumulation/Distribution Line — volume-weighted buying/selling pressure",
    "volume_ratio": "current volume / SMA(volume). Above 2 = volume spike",
    "volume_sma": "moving average of volume",
}
