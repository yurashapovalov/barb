"""Time functions: dayofweek, dayname, hour, minute, month, monthname, year, date, day, quarter."""

import pandas as pd

TIME_FUNCTIONS = {
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

TIME_SIGNATURES = {
    "dayofweek": "dayofweek()",
    "dayname": "dayname()",
    "hour": "hour()",
    "minute": "minute()",
    "month": "month()",
    "monthname": "monthname()",
    "year": "year()",
    "date": "date()",
    "day": "day()",
    "quarter": "quarter()",
}

TIME_DESCRIPTIONS = {
    "dayofweek": "0=Mon, 1=Tue, ..., 4=Fri",
    "dayname": "Monday, Tuesday, ...",
    "hour": "0-23",
    "minute": "0-59",
    "month": "1-12",
    "monthname": "January, February, ...",
    "year": "e.g. 2024",
    "date": "date object",
    "day": "day of month (1-31)",
    "quarter": "1-4",
}
