"""Rolling window functions: rolling_mean/sum/max/min/std/count, ema."""

WINDOW_FUNCTIONS = {
    "rolling_mean": lambda df, col, n: col.rolling(int(n)).mean(),
    "rolling_sum": lambda df, col, n: col.rolling(int(n)).sum(),
    "rolling_max": lambda df, col, n: col.rolling(int(n)).max(),
    "rolling_min": lambda df, col, n: col.rolling(int(n)).min(),
    "rolling_std": lambda df, col, n: col.rolling(int(n)).std(),
    "rolling_count": lambda df, cond, n: cond.astype(int).rolling(int(n)).sum(),
    "ema": lambda df, col, n: col.ewm(span=int(n), adjust=False).mean(),
}

WINDOW_SIGNATURES = {
    "rolling_mean": "rolling_mean(col, n)",
    "rolling_sum": "rolling_sum(col, n)",
    "rolling_max": "rolling_max(col, n)",
    "rolling_min": "rolling_min(col, n)",
    "rolling_std": "rolling_std(col, n)",
    "rolling_count": "rolling_count(cond, n)",
    "ema": "ema(col, n)",
}
