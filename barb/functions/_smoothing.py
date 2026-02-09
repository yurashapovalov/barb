"""Wilder's smoothing (RMA) — foundation for RSI, ATR, ADX.

NOT the same as pandas ewm(alpha=1/n, adjust=False).
The SMA seed is what makes TradingView values match.
"""

import numpy as np
import pandas as pd


def wilder_smooth(series: pd.Series, n: int) -> pd.Series:
    """Wilder's smoothing — exact TradingView ta.rma() match.

    First value = SMA of first n non-NaN points.
    Subsequent: rma[t] = (1/n) * value[t] + (1 - 1/n) * rma[t-1]
    """
    n = int(n)
    values = series.values
    result = np.full(len(values), np.nan)

    # Collect first n non-NaN values for SMA seed
    non_nan = []
    seed_idx = -1
    for i in range(len(values)):
        if not np.isnan(values[i]):
            non_nan.append(values[i])
            if len(non_nan) == n:
                seed_idx = i
                break

    if seed_idx == -1:
        return pd.Series(result, index=series.index)

    result[seed_idx] = np.mean(non_nan)

    # Recursive Wilder's: rma[t] = α * val[t] + (1 - α) * rma[t-1]
    alpha = 1.0 / n
    for i in range(seed_idx + 1, len(values)):
        if np.isnan(values[i]):
            result[i] = result[i - 1]
        else:
            result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]

    return pd.Series(result, index=series.index)
