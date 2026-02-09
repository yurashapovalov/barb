"""Aggregate functions: mean, sum, max, min, std, median, count, percentile, correlation, last."""

import numpy as np

AGGREGATE_FUNCTIONS = {
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
}

# Aggregate functions allowed in group_by context.
# Keys = Barb names, values = pandas agg method names.
AGGREGATE_FUNCS: dict[str, str] = {
    "mean": "mean", "sum": "sum", "max": "max", "min": "min",
    "std": "std", "median": "median",
}

AGGREGATE_SIGNATURES = {
    "mean": "mean(col)",
    "sum": "sum(col)",
    "max": "max(col)",
    "min": "min(col)",
    "std": "std(col)",
    "median": "median(col)",
    "count": "count()",
    "percentile": "percentile(col, p)",
    "correlation": "correlation(col1, col2)",
    "last": "last(col)",
}
