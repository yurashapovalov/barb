"""Trend functions: MACD, ADX, SuperTrend, Parabolic SAR."""

import numpy as np
import pandas as pd

from barb.functions._smoothing import wilder_smooth
from barb.functions.volatility import _atr, _tr

# --- MACD ---


def _macd(df, col, fast=12, slow=26):
    """MACD line = EMA(fast) - EMA(slow). Standard EMA, not Wilder's."""
    fast_ema = col.ewm(span=int(fast), adjust=False).mean()
    slow_ema = col.ewm(span=int(slow), adjust=False).mean()
    return fast_ema - slow_ema


def _macd_signal(df, col, fast=12, slow=26, sig=9):
    """MACD signal line = EMA(MACD, sig)."""
    macd_line = _macd(df, col, fast, slow)
    return macd_line.ewm(span=int(sig), adjust=False).mean()


def _macd_hist(df, col, fast=12, slow=26, sig=9):
    """MACD histogram = MACD - Signal."""
    macd_line = _macd(df, col, fast, slow)
    signal = macd_line.ewm(span=int(sig), adjust=False).mean()
    return macd_line - signal


# --- ADX / Directional Movement ---


def _adx_system(df, n=14):
    """Compute +DI, -DI, ADX — full Directional Movement System.

    Double Wilder's smoothing: smooth DM/TR, then smooth DX.
    Total warmup = 2n - 1 bars.
    """
    n = int(n)
    high, low = df["high"], df["low"]

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = pd.Series(0.0, index=df.index)
    minus_dm = pd.Series(0.0, index=df.index)

    plus_mask = (up_move > down_move) & (up_move > 0)
    minus_mask = (down_move > up_move) & (down_move > 0)
    plus_dm[plus_mask] = up_move[plus_mask]
    minus_dm[minus_mask] = down_move[minus_mask]

    tr = _tr(df)
    smoothed_tr = wilder_smooth(tr, n)
    smoothed_plus = wilder_smooth(plus_dm, n)
    smoothed_minus = wilder_smooth(minus_dm, n)

    plus_di = smoothed_plus / smoothed_tr * 100
    minus_di = smoothed_minus / smoothed_tr * 100

    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    adx = wilder_smooth(dx, n)

    return plus_di, minus_di, adx


def _adx(df, n=14):
    """Average Directional Index — double Wilder's smoothing."""
    _, _, adx = _adx_system(df, n)
    return adx


def _plus_di(df, n=14):
    """+DI — positive Directional Indicator."""
    plus_di, _, _ = _adx_system(df, n)
    return plus_di


def _minus_di(df, n=14):
    """-DI — negative Directional Indicator."""
    _, minus_di, _ = _adx_system(df, n)
    return minus_di


# --- SuperTrend ---


def _supertrend_system(df, n, mult):
    """Core SuperTrend: returns (value Series, direction Series).

    Direction: 1=uptrend, -1=downtrend (inverted from TV convention).
    """
    n = int(n)
    mult = float(mult)
    atr_vals = _atr(df, n).values
    hl2 = ((df["high"] + df["low"]) / 2).values
    close = df["close"].values
    length = len(df)

    upper = (hl2 + mult * atr_vals).copy()
    lower = (hl2 - mult * atr_vals).copy()

    tv_dir = np.full(length, np.nan)
    st = np.full(length, np.nan)

    for i in range(1, length):
        if np.isnan(atr_vals[i]):
            continue

        # Clamping: ratchet bands toward price
        if not np.isnan(lower[i - 1]):
            if not (lower[i] > lower[i - 1] or close[i - 1] < lower[i - 1]):
                lower[i] = lower[i - 1]
        if not np.isnan(upper[i - 1]):
            if not (upper[i] < upper[i - 1] or close[i - 1] > upper[i - 1]):
                upper[i] = upper[i - 1]

        # Direction (TV: 1=down, -1=up)
        if np.isnan(atr_vals[i - 1]) or np.isnan(st[i - 1]):
            tv_dir[i] = 1
        elif st[i - 1] == upper[i - 1]:
            tv_dir[i] = -1 if close[i] > upper[i] else 1
        else:
            tv_dir[i] = 1 if close[i] < lower[i] else -1

        st[i] = lower[i] if tv_dir[i] == -1 else upper[i]

    # Our convention: 1=up, -1=down (negate TV)
    our_dir = np.where(np.isnan(st), np.nan, -tv_dir)

    return pd.Series(st, index=df.index), pd.Series(our_dir, index=df.index)


def _supertrend(df, n=10, mult=3.0):
    """SuperTrend value — ATR-based trend line."""
    value, _ = _supertrend_system(df, n, mult)
    return value


def _supertrend_dir(df, n=10, mult=3.0):
    """SuperTrend direction: 1=uptrend, -1=downtrend."""
    _, direction = _supertrend_system(df, n, mult)
    return direction


# --- Parabolic SAR ---


def _sar(df, accel=0.02, max_accel=0.2):
    """Parabolic SAR — TradingView ta.sar() match.

    Iterative: acceleration factor increases on new extremes,
    flips when price crosses SAR.
    """
    start = float(accel)
    max_af = float(max_accel)
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    n = len(df)

    result = np.full(n, np.nan)
    if n < 2:
        return pd.Series(result, index=df.index)

    # Init direction from first two bars
    is_long = close[1] >= close[0]
    af = start

    if is_long:
        result[0] = low[0]
        ep = high[0]
    else:
        result[0] = high[0]
        ep = low[0]

    for i in range(1, n):
        sar = result[i - 1] + af * (ep - result[i - 1])

        # Clamp: SAR can't penetrate last 2 bars
        if is_long:
            sar = min(sar, low[i - 1])
            if i >= 2:
                sar = min(sar, low[i - 2])
        else:
            sar = max(sar, high[i - 1])
            if i >= 2:
                sar = max(sar, high[i - 2])

        # Check reversal
        if is_long and low[i] < sar:
            is_long = False
            sar = ep
            ep = low[i]
            af = start
        elif not is_long and high[i] > sar:
            is_long = True
            sar = ep
            ep = high[i]
            af = start
        else:
            # Update extreme point and acceleration
            if is_long:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + start, max_af)
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + start, max_af)

        result[i] = sar

    return pd.Series(result, index=df.index)


TREND_FUNCTIONS = {
    "macd": _macd,
    "macd_signal": _macd_signal,
    "macd_hist": _macd_hist,
    "adx": _adx,
    "plus_di": _plus_di,
    "minus_di": _minus_di,
    "supertrend": _supertrend,
    "supertrend_dir": _supertrend_dir,
    "sar": _sar,
}

TREND_SIGNATURES = {
    "macd": "macd(col, fast=12, slow=26)",
    "macd_signal": "macd_signal(col, fast=12, slow=26, sig=9)",
    "macd_hist": "macd_hist(col, fast=12, slow=26, sig=9)",
    "adx": "adx(n=14)",
    "plus_di": "plus_di(n=14)",
    "minus_di": "minus_di(n=14)",
    "supertrend": "supertrend(n=10, mult=3.0)",
    "supertrend_dir": "supertrend_dir(n=10, mult=3.0)",
    "sar": "sar(accel=0.02, max_accel=0.2)",
}

TREND_DESCRIPTIONS = {
    "macd": "MACD line = EMA(fast) - EMA(slow). Positive = bullish momentum",
    "macd_signal": "MACD signal line = EMA of MACD. Crossovers = trade signals",
    "macd_hist": "MACD histogram = MACD - Signal. Momentum direction and strength",
    "adx": "Average Directional Index (0-100). Above 25 = trending, below 20 = ranging",
    "plus_di": "+DI — bullish directional strength. Compare with -DI for trend direction",
    "minus_di": "-DI — bearish directional strength. Compare with +DI for trend direction",
    "supertrend": "SuperTrend value — ATR-based trend-following line",
    "supertrend_dir": "SuperTrend direction: 1 = uptrend, -1 = downtrend",
    "sar": "Parabolic SAR — trailing stop that flips on reversal",
}
