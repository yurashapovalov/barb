"""Oscillator functions: rsi, stoch_k, stoch_d, cci, williams_r, mfi, roc, momentum."""

from barb.functions._smoothing import wilder_smooth


def _rsi(df, col, n=14):
    """RSI with Wilder's smoothing — exact TradingView ta.rsi() match."""
    n = int(n)
    delta = col.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = wilder_smooth(gain, n)
    avg_loss = wilder_smooth(loss, n)

    rs = avg_gain / avg_loss
    rsi = 100 - 100 / (1 + rs)

    # Edge case: all gains (avg_loss = 0) → RSI = 100
    rsi = rsi.where(avg_loss != 0, 100.0)

    return rsi


def _stoch_k(df, n=14):
    """Stochastic %K — position of close within high/low range.

    Default n=14 matches TradingView (NOT ta-lib which defaults to 5).
    """
    n = int(n)
    lowest = df["low"].rolling(n).min()
    highest = df["high"].rolling(n).max()
    return (df["close"] - lowest) / (highest - lowest) * 100


def _stoch_d(df, n=14, smooth=3):
    """%D = SMA(%K, smooth). Default n=14, smooth=3 matches TradingView."""
    return _stoch_k(df, n).rolling(int(smooth)).mean()


def _cci(df, n=20):
    """CCI = (TP - SMA(TP)) / (0.015 * MeanDeviation).

    Uses MEAN deviation, NOT standard deviation.
    Default n=20 matches TradingView (NOT ta-lib which defaults to 14).
    """
    n = int(n)
    tp = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = tp.rolling(n).mean()
    mean_dev = tp.rolling(n).apply(lambda x: abs(x - x.mean()).mean(), raw=True)
    return (tp - sma_tp) / (0.015 * mean_dev)


def _williams_r(df, n=14):
    """Williams %R — range -100..0."""
    n = int(n)
    highest = df["high"].rolling(n).max()
    lowest = df["low"].rolling(n).min()
    return (highest - df["close"]) / (highest - lowest) * -100


def _mfi(df, n=14):
    """Money Flow Index — uses rolling sums, NOT exponential smoothing."""
    n = int(n)
    tp = (df["high"] + df["low"] + df["close"]) / 3
    rmf = tp * df["volume"]
    direction = tp.diff()
    pos_flow = rmf.where(direction > 0, 0.0).rolling(n).sum()
    neg_flow = rmf.where(direction < 0, 0.0).rolling(n).sum()
    return 100 - 100 / (1 + pos_flow / neg_flow)


def _roc(df, col, n=1):
    """Rate of Change — percentage change over n bars."""
    n = int(n)
    prev = col.shift(n)
    return (col - prev) / prev * 100


def _momentum(df, col, n=10):
    """Momentum — absolute change over n bars."""
    return col - col.shift(int(n))


OSCILLATOR_FUNCTIONS = {
    "rsi": _rsi,
    "stoch_k": _stoch_k,
    "stoch_d": _stoch_d,
    "cci": _cci,
    "williams_r": _williams_r,
    "mfi": _mfi,
    "roc": _roc,
    "momentum": _momentum,
}

OSCILLATOR_SIGNATURES = {
    "rsi": "rsi(col, n=14)",
    "stoch_k": "stoch_k(n=14)",
    "stoch_d": "stoch_d(n=14, smooth=3)",
    "cci": "cci(n=20)",
    "williams_r": "williams_r(n=14)",
    "mfi": "mfi(n=14)",
    "roc": "roc(col, n=1)",
    "momentum": "momentum(col, n=10)",
}
