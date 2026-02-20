"""Shared data operations for OHLCV DataFrames.

Reusable building blocks: session/period filtering, resampling, timeframe
constants. Used by query engine, backtest engine, and future tools (screener).
"""

import re

import pandas as pd


class BarbError(Exception):
    """Raised when execution fails (query, backtest, or any barb operation)."""

    def __init__(
        self,
        message: str,
        error_type: str = "BarbError",
        step: str = "",
        expression: str = "",
    ):
        super().__init__(message)
        self.error_type = error_type
        self.step = step
        self.expression = expression


# Valid values for the "from" field
TIMEFRAMES = {
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "daily",
    "weekly",
    "monthly",
    "quarterly",
    "yearly",
}

# Resample rules for pandas
RESAMPLE_RULES = {
    "1m": None,  # no resampling
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "h",
    "2h": "2h",
    "4h": "4h",
    "daily": "D",
    "weekly": "W",
    "monthly": "ME",
    "quarterly": "QE",
    "yearly": "YE",
}

# Timeframes that need both date and time columns
INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}


def filter_session(
    df: pd.DataFrame,
    session: str,
    sessions: dict,
) -> tuple[pd.DataFrame, str | None]:
    """Filter by session time range (RTH, ETH, etc.)."""
    key = session.upper()
    if key not in sessions:
        return df, f"Unknown session '{session}', using all data"

    start_str, end_str = sessions[key]
    start_t = pd.Timestamp(start_str).time()
    end_t = pd.Timestamp(end_str).time()

    # Wrap-around sessions (18:00-09:30) span midnight.
    # Filter: time >= start OR time < end (not AND).
    if start_t > end_t:
        mask = (df.index.time >= start_t) | (df.index.time < end_t)
    else:
        mask = (df.index.time >= start_t) & (df.index.time < end_t)

    return df[mask], None


def add_session_id(df: pd.DataFrame, session_times: tuple[str, str]) -> pd.DataFrame:
    """Add __session_id column based on known session start time.

    For wrap-around sessions (ETH 18:00→17:00): bars at/after start_time
    belong to the next calendar date's session.
    For normal sessions (RTH 09:30→16:00): session = calendar date.
    """
    start_t = pd.Timestamp(session_times[0]).time()
    end_t = pd.Timestamp(session_times[1]).time()

    df = df.copy()
    if start_t > end_t:
        # Wrap-around: Monday 18:00 → Tuesday's session, Tuesday 09:00 → Tuesday's session
        norm = df.index.normalize()
        after_start = df.index.time >= start_t
        sid = pd.Series(norm, index=df.index)
        sid[after_start] += pd.Timedelta(days=1)
        df["__session_id"] = sid
    else:
        df["__session_id"] = df.index.normalize()

    return df


_RELATIVE_PERIODS = {"last_year", "last_month", "last_week"}
_LAST_N_RE = re.compile(r"^last_(\d+)$")
# Year "2024", month "2024-03", date "2024-03-15", range "2024-01-01:2024-06-30"
_PERIOD_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def filter_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Filter by date range."""
    if df.empty:
        return df

    if ":" in period:
        # Range: "2024-01:2024-06", "2023:", ":2024"
        parts = period.split(":", 1)
        start, end = parts[0], parts[1]

        # Validate non-empty parts
        if start and not _PERIOD_RE.match(start):
            raise BarbError(
                f"Invalid period start '{start}'. Use YYYY, YYYY-MM, or YYYY-MM-DD",
                error_type="ValidationError",
                step="period",
                expression=period,
            )
        if end and not _PERIOD_RE.match(end):
            raise BarbError(
                f"Invalid period end '{end}'. Use YYYY, YYYY-MM, or YYYY-MM-DD",
                error_type="ValidationError",
                step="period",
                expression=period,
            )

        # Open-ended ranges: "2023:" or ":2024"
        return df.loc[start if start else None : end if end else None]

    if period in _RELATIVE_PERIODS:
        offsets = {
            "last_year": pd.DateOffset(years=1),
            "last_month": pd.DateOffset(months=1),
            "last_week": pd.DateOffset(weeks=1),
        }
        cutoff = df.index[-1] - offsets[period]
        return df[df.index >= cutoff]

    # Count-based: "last_50" = last 50 trading days in the data
    m = _LAST_N_RE.match(period)
    if m:
        n = int(m.group(1))
        unique_dates = df.index.normalize().unique()
        if n >= len(unique_dates):
            return df
        cutoff = unique_dates[-n]
        return df[df.index >= cutoff]

    # Year: "2024" or month: "2024-01"
    if not _PERIOD_RE.match(period):
        raise BarbError(
            f"Invalid period '{period}'. "
            f"Valid: 'YYYY', 'YYYY-MM', 'YYYY-MM-DD', 'YYYY-MM-DD:YYYY-MM-DD', "
            f"'last_year', 'last_month', 'last_week', 'last_N' (e.g. 'last_50')",
            error_type="ValidationError",
            step="period",
            expression=period,
        )
    # Slice to always return a DataFrame (not a Series for single-date match)
    return df.loc[period:period]


def resample(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample to target timeframe."""
    rule = RESAMPLE_RULES.get(timeframe)
    if not rule:
        return df

    resampled = df.resample(rule).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )
    # Drop periods with no data. Can't use dropna(how="all") because
    # volume.sum() returns 0 for empty groups, not NaN.
    return resampled.dropna(subset=["open"])
