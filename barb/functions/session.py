"""Session-aware functions: session_high, session_low, session_open, session_close.

Uses __session_id column computed from known session times (set by ops.add_session_id).
Falls back to time-gap detection when no session context is available.
"""

import pandas as pd


def _session_id(df):
    """Get session ID for each bar.

    If __session_id exists (set by interpreter from config), use it.
    Otherwise fall back to gap detection (> 90 min = new session).
    """
    if "__session_id" in df.columns:
        return df["__session_id"]
    # Fallback: no session context (e.g. raw data without session filter)
    time_diff = df.index.to_series().diff()
    return (time_diff > pd.Timedelta(minutes=90)).cumsum()


def _session_high(df):
    return df.groupby(_session_id(df))["high"].transform("max")


def _session_low(df):
    return df.groupby(_session_id(df))["low"].transform("min")


def _session_open(df):
    return df.groupby(_session_id(df))["open"].transform("first")


def _session_close(df):
    return df.groupby(_session_id(df))["close"].transform("last")


SESSION_FUNCTIONS = {
    "session_high": _session_high,
    "session_low": _session_low,
    "session_open": _session_open,
    "session_close": _session_close,
}

SESSION_SIGNATURES = {
    "session_high": "session_high()",
    "session_low": "session_low()",
    "session_open": "session_open()",
    "session_close": "session_close()",
}

SESSION_DESCRIPTIONS = {
    "session_high": "highest high in the current trading session",
    "session_low": "lowest low in the current trading session",
    "session_open": "open of the first bar in the current session",
    "session_close": "close of the last bar in the current session",
}
