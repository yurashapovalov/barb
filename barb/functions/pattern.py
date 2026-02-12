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


def _rising(df, col, n=1):
    """True if col has risen for n bars straight. Matches ta.rising() in Pine."""
    n = int(n)
    result = pd.Series(True, index=col.index)
    for i in range(1, n + 1):
        result = result & (col > col.shift(i))
    return result


def _falling(df, col, n=1):
    """True if col has fallen for n bars straight. Matches ta.falling() in Pine."""
    n = int(n)
    result = pd.Series(True, index=col.index)
    for i in range(1, n + 1):
        result = result & (col < col.shift(i))
    return result


def _valuewhen(df, cond, col, n=0):
    """Value of col when cond was true, n-th occurrence back (0=most recent)."""
    n = int(n)
    result = pd.Series(np.nan, index=cond.index)
    occurrences = []
    for i in range(len(cond)):
        if cond.iloc[i]:
            occurrences.append(i)
        if len(occurrences) > n:
            idx = occurrences[-(n + 1)]
            result.iloc[i] = col.iloc[idx]
    return result


def _pivothigh(df, n_left=5, n_right=5):
    """Pivot high: high[i] is higher than n_left bars before and n_right bars after.

    Returns high value at pivot, NaN elsewhere. Lags by n_right bars.
    """
    n_left, n_right = int(n_left), int(n_right)
    high = df["high"]
    result = pd.Series(np.nan, index=high.index)
    for i in range(n_left, len(high) - n_right):
        val = high.iloc[i]
        left = high.iloc[i - n_left : i]
        right = high.iloc[i + 1 : i + n_right + 1]
        if (val > left).all() and (val > right).all():
            # Report at the confirmation bar (n_right bars later)
            result.iloc[i + n_right] = val
    return result


def _pivotlow(df, n_left=5, n_right=5):
    """Pivot low: low[i] is lower than n_left bars before and n_right bars after.

    Returns low value at pivot, NaN elsewhere. Lags by n_right bars.
    """
    n_left, n_right = int(n_left), int(n_right)
    low = df["low"]
    result = pd.Series(np.nan, index=low.index)
    for i in range(n_left, len(low) - n_right):
        val = low.iloc[i]
        left = low.iloc[i - n_left : i]
        right = low.iloc[i + 1 : i + n_right + 1]
        if (val < left).all() and (val < right).all():
            result.iloc[i + n_right] = val
    return result


PATTERN_FUNCTIONS = {
    "streak": _streak,
    "bars_since": _bars_since,
    "rank": lambda df, col: col.rank(pct=True),
    "rising": _rising,
    "falling": _falling,
    "valuewhen": _valuewhen,
    "pivothigh": _pivothigh,
    "pivotlow": _pivotlow,
}

PATTERN_SIGNATURES = {
    "streak": "streak(cond)",
    "bars_since": "bars_since(cond)",
    "rank": "rank(col)",
    "rising": "rising(col, n=1)",
    "falling": "falling(col, n=1)",
    "valuewhen": "valuewhen(cond, col, n=0)",
    "pivothigh": "pivothigh(n_left=5, n_right=5)",
    "pivotlow": "pivotlow(n_left=5, n_right=5)",
}

PATTERN_DESCRIPTIONS = {
    "streak": "consecutive bars where condition is true, resets on false",
    "bars_since": "number of bars since condition was last true",
    "rank": "percentile rank (0-1) within the column",
    "rising": "true if value increased for n bars straight",
    "falling": "true if value decreased for n bars straight",
    "valuewhen": "value of col when condition was true, n-th occurrence back",
    "pivothigh": "pivot high: local high confirmed after n_right bars",
    "pivotlow": "pivot low: local low confirmed after n_right bars",
}
