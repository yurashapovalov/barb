"""Trading convenience functions: gap, body, crossover, etc.

Short wrappers that give Claude a trading vocabulary.
Each function is 1-2 lines — no complex logic, pure sugar.
"""

import pandas as pd

# -- Price helpers --

def _gap(df):
    return df["open"] - df["close"].shift(1)


def _gap_pct(df):
    prev_close = df["close"].shift(1)
    return (df["open"] - prev_close) / prev_close * 100


def _change(df, col, n=1):
    n = int(n)
    return col - col.shift(n)


def _change_pct(df, col, n=1):
    n = int(n)
    prev = col.shift(n)
    return (col - prev) / prev * 100


def _range(df):
    return df["high"] - df["low"]


def _range_pct(df):
    return (df["high"] - df["low"]) / df["low"] * 100


def _midpoint(df):
    return (df["high"] + df["low"]) / 2


def _typical_price(df):
    return (df["high"] + df["low"] + df["close"]) / 3


# -- Candle helpers --

def _body(df):
    return df["close"] - df["open"]


def _body_pct(df):
    return (df["close"] - df["open"]) / df["open"] * 100


def _upper_wick(df):
    return df["high"] - pd.concat([df["open"], df["close"]], axis=1).max(axis=1)


def _lower_wick(df):
    return pd.concat([df["open"], df["close"]], axis=1).min(axis=1) - df["low"]


def _green(df):
    return df["close"] > df["open"]


def _red(df):
    return df["close"] < df["open"]


def _doji(df, threshold=0.1):
    body = (df["close"] - df["open"]).abs()
    bar_range = df["high"] - df["low"]
    return body / bar_range < float(threshold)


def _inside_bar(df):
    return (df["high"] < df["high"].shift(1)) & (df["low"] > df["low"].shift(1))


def _outside_bar(df):
    return (df["high"] > df["high"].shift(1)) & (df["low"] < df["low"].shift(1))


# -- Signal helpers --

def _crossover(df, a, b):
    return (a.shift(1) <= b.shift(1)) & (a > b)


def _crossunder(df, a, b):
    return (a.shift(1) >= b.shift(1)) & (a < b)


CONVENIENCE_FUNCTIONS = {
    # Price
    "gap": _gap,
    "gap_pct": _gap_pct,
    "change": _change,
    "change_pct": _change_pct,
    "range": _range,
    "range_pct": _range_pct,
    "midpoint": _midpoint,
    "typical_price": _typical_price,
    # Candle
    "body": _body,
    "body_pct": _body_pct,
    "upper_wick": _upper_wick,
    "lower_wick": _lower_wick,
    "green": _green,
    "red": _red,
    "doji": _doji,
    "inside_bar": _inside_bar,
    "outside_bar": _outside_bar,
    # Signal
    "crossover": _crossover,
    "crossunder": _crossunder,
}

CONVENIENCE_SIGNATURES = {
    # Price
    "gap": "gap()",
    "gap_pct": "gap_pct()",
    "change": "change(col, n=1)",
    "change_pct": "change_pct(col, n=1)",
    "range": "range()",
    "range_pct": "range_pct()",
    "midpoint": "midpoint()",
    "typical_price": "typical_price()",
    # Candle
    "body": "body()",
    "body_pct": "body_pct()",
    "upper_wick": "upper_wick()",
    "lower_wick": "lower_wick()",
    "green": "green()",
    "red": "red()",
    "doji": "doji(threshold=0.1)",
    "inside_bar": "inside_bar()",
    "outside_bar": "outside_bar()",
    # Signal
    "crossover": "crossover(a, b)",
    "crossunder": "crossunder(a, b)",
}
