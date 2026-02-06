"""All Barb Script functions.

Plain dict mapping names to callables. Every function receives (df, *args)
where df is the current DataFrame — needed for time functions and count().
"""

from collections.abc import Callable

import numpy as np
import pandas as pd


def _if(df, cond, then, else_):
    """Element-wise conditional: if(cond, then, else)."""
    if isinstance(cond, pd.Series):
        return pd.Series(np.where(cond, then, else_), index=cond.index)
    return then if cond else else_


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


# -- Function registry --
# Every function signature: (df, *args) -> Series | scalar
# df is always the first arg (passed by the expression evaluator)

FUNCTIONS: dict[str, Callable] = {
    # Scalar
    "abs": lambda df, x: x.abs() if isinstance(x, pd.Series) else abs(x),
    "log": lambda df, x: np.log(x),
    "sqrt": lambda df, x: np.sqrt(x),
    "sign": lambda df, x: np.sign(x),
    "round": lambda df, x, n=0: (x.round(int(n)) if isinstance(x, pd.Series) else round(x, int(n))),
    "if": _if,

    # Lag
    "prev": lambda df, col, n=1: col.shift(int(n)),
    "next": lambda df, col, n=1: col.shift(-int(n)),

    # Window
    "rolling_mean": lambda df, col, n: col.rolling(int(n)).mean(),
    "rolling_sum": lambda df, col, n: col.rolling(int(n)).sum(),
    "rolling_max": lambda df, col, n: col.rolling(int(n)).max(),
    "rolling_min": lambda df, col, n: col.rolling(int(n)).min(),
    "rolling_std": lambda df, col, n: col.rolling(int(n)).std(),
    "rolling_count": lambda df, cond, n: cond.astype(int).rolling(int(n)).sum(),
    "ema": lambda df, col, n: col.ewm(span=int(n), adjust=False).mean(),

    # Cumulative
    "cummax": lambda df, col: col.cummax(),
    "cummin": lambda df, col: col.cummin(),
    "cumsum": lambda df, col: col.cumsum(),

    # Pattern
    "streak": _streak,
    "bars_since": _bars_since,
    "rank": lambda df, col: col.rank(pct=True),

    # Aggregate
    "mean": lambda df, col: col.mean(),
    "sum": lambda df, col: col.sum(),
    "max": lambda df, col: col.max(),
    "min": lambda df, col: col.min(),
    "std": lambda df, col: col.std(),
    "median": lambda df, col: col.median(),
    "count": lambda df: len(df),
    "percentile": lambda df, col, p: col.quantile(float(p)),
    "correlation": lambda df, col1, col2: col1.corr(col2),
    "last": lambda df, col: col.iloc[-1] if len(col) > 0 else np.nan,

    # Time (extract from DatetimeIndex)
    "dayofweek": lambda df: pd.Series(df.index.dayofweek, index=df.index),
    "dayname": lambda df: pd.Series(df.index.day_name(), index=df.index),
    "hour": lambda df: pd.Series(df.index.hour, index=df.index),
    "minute": lambda df: pd.Series(df.index.minute, index=df.index),
    "month": lambda df: pd.Series(df.index.month, index=df.index),
    "monthname": lambda df: pd.Series(df.index.month_name(), index=df.index),
    "year": lambda df: pd.Series(df.index.year, index=df.index),
    "date": lambda df: pd.Series(df.index.date, index=df.index),
    "day": lambda df: pd.Series(df.index.day, index=df.index),
    "quarter": lambda df: pd.Series(df.index.quarter, index=df.index),
}

# Aggregate functions allowed in group_by context.
# Keys = Barb names, values = pandas agg method names.
AGGREGATE_FUNCS: dict[str, str] = {
    "mean": "mean", "sum": "sum", "max": "max", "min": "min",
    "std": "std", "median": "median",
}
