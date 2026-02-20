"""Time functions — from largest to smallest unit.

year, quarter, month, date, day_of_month, dayofweek, hour, minute.
"""

import datetime

import pandas as pd


def _date(df, *args):
    """date() → Series of dates; date('2024-01-15') → date literal for comparison."""
    if not args:
        return pd.Series(df.index.date, index=df.index)
    return datetime.datetime.strptime(args[0], "%Y-%m-%d").date()


TIME_FUNCTIONS = {
    # Large units
    "year": lambda df: pd.Series(df.index.year, index=df.index),
    "quarter": lambda df: pd.Series(df.index.quarter, index=df.index),
    "month": lambda df: pd.Series(df.index.month, index=df.index),
    # Date
    "date": _date,
    "day_of_month": lambda df: pd.Series(df.index.day, index=df.index),
    "dayofweek": lambda df: pd.Series(df.index.dayofweek, index=df.index),
    # Time
    "hour": lambda df: pd.Series(df.index.hour, index=df.index),
    "minute": lambda df: pd.Series(df.index.minute, index=df.index),
}

TIME_SIGNATURES = {
    "year": "year()",
    "quarter": "quarter()",
    "month": "month()",
    "date": "date(s?)",
    "day_of_month": "day_of_month()",
    "dayofweek": "dayofweek()",
    "hour": "hour()",
    "minute": "minute()",
}

TIME_DESCRIPTIONS = {
    "year": "e.g. 2024",
    "quarter": "1-4",
    "month": "1-12",
    "date": "date() → date series; date('2024-01-15') → date literal for comparison",
    "day_of_month": "1-31",
    "dayofweek": "0=Monday, 4=Friday",
    "hour": "0-23",
    "minute": "0-59",
}
