"""Rolling window functions: moving averages, rolling stats."""

import numpy as np

from barb.functions._smoothing import wilder_smooth


def _wma(df, col, n):
    """Weighted Moving Average — linear weights, recent bars weigh more."""
    n = int(n)
    weights = np.arange(1, n + 1, dtype=float)
    return col.rolling(n).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def _hma(df, col, n):
    """Hull Moving Average — fast MA with minimal lag.

    HMA(n) = WMA(2 * WMA(n/2) - WMA(n), sqrt(n))
    """
    n = int(n)
    half_n = max(int(n / 2), 1)
    sqrt_n = max(int(np.sqrt(n)), 1)

    weights_half = np.arange(1, half_n + 1, dtype=float)
    weights_full = np.arange(1, n + 1, dtype=float)
    weights_sqrt = np.arange(1, sqrt_n + 1, dtype=float)

    wma_half = col.rolling(half_n).apply(
        lambda x: np.dot(x, weights_half) / weights_half.sum(), raw=True
    )
    wma_full = col.rolling(n).apply(
        lambda x: np.dot(x, weights_full) / weights_full.sum(), raw=True
    )

    diff = 2 * wma_half - wma_full
    return diff.rolling(sqrt_n).apply(
        lambda x: np.dot(x, weights_sqrt) / weights_sqrt.sum(), raw=True
    )


def _vwma(df, n=20):
    """Volume Weighted Moving Average — SMA of (close * volume) / SMA of volume."""
    n = int(n)
    return (df["close"] * df["volume"]).rolling(n).sum() / df["volume"].rolling(n).sum()


def _rma(df, col, n):
    """Wilder's smoothing (RMA) — exposed as public function. Same as ta.rma() in Pine."""
    return wilder_smooth(col, int(n))


WINDOW_FUNCTIONS = {
    "rolling_mean": lambda df, col, n: col.rolling(int(n)).mean(),
    "rolling_sum": lambda df, col, n: col.rolling(int(n)).sum(),
    "rolling_max": lambda df, col, n: col.rolling(int(n)).max(),
    "rolling_min": lambda df, col, n: col.rolling(int(n)).min(),
    "rolling_std": lambda df, col, n: col.rolling(int(n)).std(),
    "rolling_count": lambda df, cond, n: cond.astype(int).rolling(int(n)).sum(),
    "ema": lambda df, col, n: col.ewm(span=int(n), adjust=False).mean(),
    "sma": lambda df, col, n: col.rolling(int(n)).mean(),
    "wma": _wma,
    "hma": _hma,
    "vwma": _vwma,
    "rma": _rma,
}

WINDOW_SIGNATURES = {
    "rolling_mean": "rolling_mean(col, n)",
    "rolling_sum": "rolling_sum(col, n)",
    "rolling_max": "rolling_max(col, n)",
    "rolling_min": "rolling_min(col, n)",
    "rolling_std": "rolling_std(col, n)",
    "rolling_count": "rolling_count(cond, n)",
    "ema": "ema(col, n)",
    "sma": "sma(col, n)",
    "wma": "wma(col, n)",
    "hma": "hma(col, n)",
    "vwma": "vwma(n=20)",
    "rma": "rma(col, n)",
}
