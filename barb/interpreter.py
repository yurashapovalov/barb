"""Barb Script interpreter.

Executes a flat JSON query against a pandas DataFrame.
10-step pipeline, fixed execution order regardless of JSON key order.
"""

import re

import pandas as pd

from barb.expressions import evaluate, ExpressionError
from barb.functions import FUNCTIONS


# Valid values for the "from" field
TIMEFRAMES = {
    "1m", "5m", "15m", "30m",
    "1h", "2h", "4h",
    "daily", "weekly", "monthly", "quarterly", "yearly",
}

# Resample rules for pandas
_RESAMPLE_RULES = {
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

# Fields allowed in a query
_VALID_FIELDS = {
    "session", "from", "period", "join", "map",
    "where", "group_by", "select", "sort", "limit",
}


class QueryError(Exception):
    """Raised when a query is invalid or execution fails."""

    def __init__(self, message: str, error_type: str = "QueryError", step: str = "", expression: str = ""):
        super().__init__(message)
        self.error_type = error_type
        self.step = step
        self.expression = expression


def execute(query: dict, df: pd.DataFrame, sessions: dict) -> dict:
    """Execute a Barb Script query.

    Args:
        query: Flat JSON query dict
        df: Minute-level DataFrame with DatetimeIndex and OHLCV columns
        sessions: {"RTH": ("09:30", "17:00"), ...}

    Returns:
        {"result": ..., "metadata": {...}, "table": [...] | None, "query": query}

    Raises:
        QueryError: On validation or execution failure
    """
    _validate(query)

    warnings = []

    # 1. SESSION — filter minute data by time of day
    session_name = query.get("session")
    if session_name:
        df, warn = _filter_session(df, session_name, sessions)
        if warn:
            warnings.append(warn)

    # 2. PERIOD — filter by date range
    period = query.get("period")
    if period:
        df = _filter_period(df, period)

    # 3. FROM — resample to target timeframe
    timeframe = query.get("from", "1m")
    if timeframe != "1m":
        df = _resample(df, timeframe)

    # 4. JOIN — attach external data (stub)
    if query.get("join"):
        pass  # TODO: implement join

    # 5. MAP — compute derived columns
    if query.get("map"):
        df = _compute_map(df, query["map"])

    # 6. WHERE — filter rows
    if query.get("where"):
        df = _filter_where(df, query["where"])

    rows_after_filter = len(df)

    # 7-8. GROUP BY + SELECT
    group_by = query.get("group_by")
    select = query.get("select", "count()")

    if group_by:
        result_df = _group_aggregate(df, group_by, select)
    else:
        result_df = _aggregate(df, select)

    # 9. SORT
    if query.get("sort") and isinstance(result_df, pd.DataFrame):
        result_df = _sort(result_df, query["sort"])

    # 10. LIMIT
    if query.get("limit") and isinstance(result_df, pd.DataFrame):
        result_df = result_df.head(query["limit"])

    return _build_response(result_df, query, rows_after_filter, session_name, timeframe, warnings)


# --- Validation ---

def _validate(query: dict):
    """Lightweight schema check."""
    unknown = set(query.keys()) - _VALID_FIELDS
    if unknown:
        raise QueryError(
            f"Unknown fields: {', '.join(unknown)}. Valid: {', '.join(sorted(_VALID_FIELDS))}",
            error_type="ValidationError", step="validate",
        )

    tf = query.get("from", "1m")
    if tf not in TIMEFRAMES:
        raise QueryError(
            f"Invalid timeframe '{tf}'. Valid: {', '.join(sorted(TIMEFRAMES))}",
            error_type="ValidationError", step="validate",
        )

    if "limit" in query and (not isinstance(query["limit"], int) or query["limit"] < 1):
        raise QueryError(
            "limit must be a positive integer",
            error_type="ValidationError", step="validate",
        )

    if "map" in query and not isinstance(query["map"], dict):
        raise QueryError(
            "map must be an object {name: expression}",
            error_type="ValidationError", step="validate",
        )


# --- Pipeline steps ---

def _filter_session(df: pd.DataFrame, session: str, sessions: dict) -> tuple[pd.DataFrame, str | None]:
    """Step 1: Filter by session time range."""
    key = session.upper()
    if key not in sessions:
        return df, f"Unknown session '{session}', using all data"

    start_str, end_str = sessions[key]
    start_t = pd.Timestamp(start_str).time()
    end_t = pd.Timestamp(end_str).time()

    # Wrap-around sessions (18:00-09:30) span midnight
    if start_t > end_t:
        mask = (df.index.time >= start_t) | (df.index.time < end_t)
    else:
        mask = (df.index.time >= start_t) & (df.index.time < end_t)

    return df[mask], None


def _filter_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Step 2: Filter by date range."""
    if ":" in period:
        # Explicit range: "2024-01-01:2024-12-31"
        start, end = period.split(":", 1)
        return df.loc[start:end]

    if period == "last_year":
        cutoff = df.index[-1] - pd.DateOffset(years=1)
        return df[df.index >= cutoff]

    if period == "last_month":
        cutoff = df.index[-1] - pd.DateOffset(months=1)
        return df[df.index >= cutoff]

    if period == "last_week":
        cutoff = df.index[-1] - pd.DateOffset(weeks=1)
        return df[df.index >= cutoff]

    # Year: "2024" or month: "2024-01"
    # Must use .loc for DatetimeIndex partial string indexing
    return df.loc[period]


def _resample(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Step 3: Resample to target timeframe."""
    rule = _RESAMPLE_RULES.get(timeframe)
    if not rule:
        return df

    resampled = df.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    })
    # Drop periods with no data. Can't use dropna(how="all") because
    # volume.sum() returns 0 for empty groups, not NaN.
    return resampled.dropna(subset=["open"])


def _compute_map(df: pd.DataFrame, map_config: dict) -> pd.DataFrame:
    """Step 5: Compute derived columns in declaration order."""
    df = df.copy()
    for name, expr in map_config.items():
        try:
            df[name] = evaluate(expr, df, FUNCTIONS)
        except ExpressionError as e:
            raise QueryError(str(e), error_type="ExpressionError", step="map", expression=expr) from e
    return df


def _filter_where(df: pd.DataFrame, where_expr: str) -> pd.DataFrame:
    """Step 6: Filter rows by boolean expression."""
    try:
        mask = evaluate(where_expr, df, FUNCTIONS)
    except ExpressionError as e:
        raise QueryError(str(e), error_type="ExpressionError", step="where", expression=where_expr) from e

    if not isinstance(mask, pd.Series):
        raise QueryError(
            f"WHERE must produce a boolean series, got {type(mask).__name__}",
            error_type="TypeError", step="where", expression=where_expr,
        )
    return df[mask]


def _group_aggregate(df: pd.DataFrame, group_by, select) -> pd.DataFrame:
    """Steps 7-8: Group and aggregate."""
    if isinstance(group_by, str):
        group_by = [group_by]
    if isinstance(select, str):
        select = [select]

    groups = df.groupby(group_by)
    result_parts = {}

    for s in select:
        col_name, value = _eval_aggregate(groups, df, s)
        result_parts[col_name] = value

    result = pd.DataFrame(result_parts)
    return result


def _aggregate(df: pd.DataFrame, select) -> float | int | dict:
    """Step 8 without grouping: aggregate to scalar(s)."""
    if isinstance(select, str):
        try:
            result = evaluate(select, df, FUNCTIONS)
        except ExpressionError as e:
            raise QueryError(str(e), error_type="ExpressionError", step="select", expression=select) from e
        return result

    # Multiple selects → dict of results
    if isinstance(select, list):
        results = {}
        for s in select:
            try:
                val = evaluate(s, df, FUNCTIONS)
            except ExpressionError as e:
                raise QueryError(str(e), error_type="ExpressionError", step="select", expression=s) from e
            col_name = _aggregate_col_name(s)
            results[col_name] = val
        return results

    return len(df)


def _eval_aggregate(groups, df: pd.DataFrame, select_expr: str) -> tuple[str, pd.Series]:
    """Evaluate one aggregate expression on grouped data."""
    col_name = _aggregate_col_name(select_expr)

    if select_expr.strip() == "count()":
        return col_name, groups.size()

    # Parse: mean(range) → func=mean, col=range
    match = re.match(r"(\w+)\((\w+)\)", select_expr.strip())
    if not match:
        raise QueryError(
            f"Cannot parse aggregate expression: '{select_expr}'",
            error_type="ParseError", step="select", expression=select_expr,
        )

    func_name, col = match.groups()
    agg_map = {
        "mean": "mean", "sum": "sum", "max": "max", "min": "min",
        "std": "std", "median": "median",
    }

    if func_name not in agg_map:
        raise QueryError(
            f"Unknown aggregate function '{func_name}' in group context",
            error_type="UnknownFunction", step="select", expression=select_expr,
        )

    return col_name, groups[col].agg(agg_map[func_name])


def _aggregate_col_name(expr: str) -> str:
    """Generate column name from aggregate expression: mean(range) → mean_range."""
    import re
    expr = expr.strip()
    if expr == "count()":
        return "count"
    match = re.match(r"(\w+)\((\w+)(?:,\s*\w+)?\)", expr)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    return expr


def _sort(df: pd.DataFrame, sort: str) -> pd.DataFrame:
    """Step 9: Sort result."""
    parts = sort.split()
    col = parts[0]
    ascending = len(parts) < 2 or parts[1].lower() != "desc"
    if col in df.columns:
        return df.sort_values(col, ascending=ascending)
    return df


def _build_response(result, query, rows, session, timeframe, warnings) -> dict:
    """Build the structured response."""
    metadata = {
        "rows": rows,
        "session": session,
        "from": timeframe,
        "warnings": warnings,
    }

    if isinstance(result, pd.DataFrame):
        table = result.reset_index().to_dict("records")
        return {
            "result": table,
            "metadata": metadata,
            "table": table,
            "query": query,
        }

    if isinstance(result, dict):
        return {
            "result": result,
            "metadata": metadata,
            "table": None,
            "query": query,
        }

    # Scalar
    # Convert numpy types to Python native for JSON serialization
    if hasattr(result, "item"):
        result = result.item()

    return {
        "result": result,
        "metadata": metadata,
        "table": None,
        "query": query,
    }
