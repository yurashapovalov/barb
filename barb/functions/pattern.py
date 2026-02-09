"""Pattern functions: streak, bars_since, rank."""

import numpy as np
import pandas as pd


def _streak(df, cond):
    """Consecutive count while condition is true. Resets to 0 on false."""
    result = pd.Series(0, index=cond.index, dtype=int)
    count = 0
    for i in range(len(cond)):
        if cond.iloc[i]:
            count += 1
        else:
            count = 0
        result.iloc[i] = count
    return result


def _bars_since(df, cond):
    """Number of bars since condition was last true. NaN if never true."""
    result = pd.Series(np.nan, index=cond.index)
    last_true = None
    for i in range(len(cond)):
        if cond.iloc[i]:
            last_true = i
        if last_true is not None:
            result.iloc[i] = i - last_true
    return result


PATTERN_FUNCTIONS = {
    "streak": _streak,
    "bars_since": _bars_since,
    "rank": lambda df, col: col.rank(pct=True),
}

PATTERN_SIGNATURES = {
    "streak": "streak(cond)",
    "bars_since": "bars_since(cond)",
    "rank": "rank(col)",
}
