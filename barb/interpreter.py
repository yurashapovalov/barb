"""Barb Script interpreter.

Executes a flat JSON query against a pandas DataFrame.
9-step pipeline, fixed execution order regardless of JSON key order:
  session → period → from → map → where → group_by → select → sort → limit
"""

import re

import pandas as pd

from barb.expressions import ExpressionError, evaluate
from barb.functions import AGGREGATE_FUNCS, FUNCTIONS
from barb.validation import validate_expressions

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
_INTRADAY_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}

# Standard OHLC column order
_OHLC_COLUMNS = ["open", "high", "low", "close"]

# Columns to preserve original precision (source data, not calculated)
_PRESERVE_PRECISION = {"open", "high", "low", "close", "volume"}

# Decimal places for calculated values (FP noise removal)
CALCULATED_PRECISION = 4

# Fields allowed in a query
_VALID_FIELDS = {
    "session",
    "from",
    "period",
    "map",
    "where",
    "group_by",
    "select",
    "sort",
    "limit",
}


class QueryError(Exception):
    """Raised when a query is invalid or execution fails."""

    def __init__(
        self,
        message: str,
        error_type: str = "QueryError",
        step: str = "",
        expression: str = "",
    ):
        super().__init__(message)
        self.error_type = error_type
        self.step = step
        self.expression = expression


def execute(query: dict, df: pd.DataFrame, sessions: dict) -> dict:
    """Execute a Barb Script query.

    Args:
        query: Flat JSON query dict
        df: DataFrame with DatetimeIndex and OHLCV columns (daily or minute)
        sessions: {"RTH": ("09:30", "17:00"), ...}

    Returns:
        {"result": ..., "metadata": {...}, "table": [...] | None, "query": query}

    Raises:
        QueryError: On validation or execution failure
    """
    _validate(query)
    validate_expressions(query)

    warnings = []

    timeframe = query.get("from", "1m")

    # 1. SESSION — filter by time of day
    session_name = query.get("session")
    if session_name:
        # Skip session filtering if data has no time component (daily bars)
        has_time = hasattr(df.index, "hour") and (df.index.hour != 0).any()
        if has_time:
            df, warn = filter_session(df, session_name, sessions)
            if warn:
                warnings.append(warn)

    # 2. PERIOD — filter by date range
    period = query.get("period")
    if period:
        df = filter_period(df, period)

    # 3. FROM — resample to target timeframe
    df = resample(df, timeframe)

    # 4. MAP — compute derived columns
    if query.get("map"):
        df = compute_map(df, query["map"])

    # 5. WHERE — filter rows
    if query.get("where"):
        df = filter_where(df, query["where"])

    rows_after_filter = len(df)

    # 6-7. GROUP BY + SELECT
    group_by = query.get("group_by")
    select_raw = query.get("select")

    # Save filtered rows before aggregation destroys them
    source_df = df

    if group_by:
        select = _normalize_select(select_raw or "count()")
        result_df = _group_aggregate(df, group_by, select)
    elif select_raw:
        select = _normalize_select(select_raw)
        result_df = _aggregate(df, select)
    else:
        result_df = df

    # 8. SORT
    if query.get("sort") and isinstance(result_df, pd.DataFrame):
        result_df = sort_df(result_df, query["sort"])

    # 9. LIMIT
    if query.get("limit") and isinstance(result_df, pd.DataFrame):
        result_df = result_df.head(query["limit"])

    return _build_response(
        result_df, query, rows_after_filter, session_name, timeframe, warnings, source_df
    )


# --- Normalization ---


def _normalize_select(select) -> str | list[str]:
    """Split comma-separated select into list: 'sum(x), sum(y)' → ['sum(x)', 'sum(y)']."""
    if isinstance(select, str) and "," in select:
        return [s.strip() for s in select.split(",") if s.strip()]
    return select


# --- Validation ---


def _validate(query: dict):
    """Lightweight schema check."""
    unknown = set(query.keys()) - _VALID_FIELDS
    if unknown:
        raise QueryError(
            f"Unknown fields: {', '.join(unknown)}. Valid: {', '.join(sorted(_VALID_FIELDS))}",
            error_type="ValidationError",
            step="validate",
        )

    tf = query.get("from", "1m")
    if tf not in TIMEFRAMES:
        raise QueryError(
            f"Invalid timeframe '{tf}'. Valid: {', '.join(sorted(TIMEFRAMES))}",
            error_type="ValidationError",
            step="validate",
        )

    if "limit" in query and (not isinstance(query["limit"], int) or query["limit"] < 1):
        raise QueryError(
            "limit must be a positive integer",
            error_type="ValidationError",
            step="validate",
        )

    if "map" in query and not isinstance(query["map"], dict):
        raise QueryError(
            "map must be an object {name: expression}",
            error_type="ValidationError",
            step="validate",
        )


# --- Pipeline steps ---


def filter_session(
    df: pd.DataFrame,
    session: str,
    sessions: dict,
) -> tuple[pd.DataFrame, str | None]:
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


_RELATIVE_PERIODS = {"last_year", "last_month", "last_week"}
# Year "2024", month "2024-03", date "2024-03-15", range "2024-01-01:2024-06-30"
_PERIOD_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def filter_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Step 2: Filter by date range."""
    if df.empty:
        return df

    if ":" in period:
        # Range: "2024-01:2024-06", "2023:", ":2024"
        parts = period.split(":", 1)
        start, end = parts[0], parts[1]

        # Validate non-empty parts
        if start and not _PERIOD_RE.match(start):
            raise QueryError(
                f"Invalid period start '{start}'. Use YYYY, YYYY-MM, or YYYY-MM-DD",
                error_type="ValidationError",
                step="period",
                expression=period,
            )
        if end and not _PERIOD_RE.match(end):
            raise QueryError(
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

    # Year: "2024" or month: "2024-01"
    if not _PERIOD_RE.match(period):
        raise QueryError(
            f"Invalid period '{period}'. "
            f"Valid: 'YYYY', 'YYYY-MM', 'YYYY-MM-DD', 'YYYY-MM-DD:YYYY-MM-DD', "
            f"'last_year', 'last_month', 'last_week'",
            error_type="ValidationError",
            step="period",
            expression=period,
        )
    return df.loc[period]


def resample(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Step 3: Resample to target timeframe."""
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


def compute_map(df: pd.DataFrame, map_config: dict) -> pd.DataFrame:
    """Step 4: Compute derived columns in declaration order."""
    df = df.copy()
    for name, expr in map_config.items():
        if not isinstance(expr, str):
            raise QueryError(
                f"map value for '{name}' must be a string expression, got {type(expr).__name__}",
                error_type="TypeError",
                step="map",
                expression=str(expr),
            )
        try:
            df[name] = evaluate(expr, df, FUNCTIONS)
        except ExpressionError as e:
            raise QueryError(
                str(e),
                error_type="ExpressionError",
                step="map",
                expression=expr,
            ) from e
    return df


def filter_where(df: pd.DataFrame, where_expr: str) -> pd.DataFrame:
    """Step 5: Filter rows by boolean expression."""
    try:
        mask = evaluate(where_expr, df, FUNCTIONS)
    except ExpressionError as e:
        raise QueryError(
            str(e),
            error_type="ExpressionError",
            step="where",
            expression=where_expr,
        ) from e

    if not isinstance(mask, pd.Series):
        raise QueryError(
            f"WHERE must produce a boolean series, got {type(mask).__name__}",
            error_type="TypeError",
            step="where",
            expression=where_expr,
        )
    return df[mask]


def _group_aggregate(df: pd.DataFrame, group_by, select) -> pd.DataFrame:
    """Steps 6-7: Group and aggregate."""
    if isinstance(group_by, str):
        group_by = [group_by]
    if isinstance(select, str):
        select = [select]

    for col in group_by:
        if col not in df.columns:
            available = ", ".join(sorted(df.columns))
            raise QueryError(
                f"Column '{col}' not found. Available: {available}",
                error_type="ValidationError",
                step="group_by",
                expression=col,
            )

    groups = df.groupby(group_by)
    result_parts = {}

    for s in select:
        col_name, value = _eval_aggregate(groups, df, s)
        result_parts[col_name] = value

    result = pd.DataFrame(result_parts)
    return result


def _aggregate(df: pd.DataFrame, select) -> float | int | dict:
    """Step 7 without grouping: aggregate to scalar(s)."""
    if isinstance(select, str):
        try:
            result = evaluate(select, df, FUNCTIONS)
        except ExpressionError as e:
            raise QueryError(
                str(e),
                error_type="ExpressionError",
                step="select",
                expression=select,
            ) from e
        return result

    # Multiple selects → dict of results
    results = {}
    for s in select:
        try:
            val = evaluate(s, df, FUNCTIONS)
        except ExpressionError as e:
            raise QueryError(
                str(e),
                error_type="ExpressionError",
                step="select",
                expression=s,
            ) from e
        col_name = _aggregate_col_name(s)
        results[col_name] = val
    return results


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
            error_type="ParseError",
            step="select",
            expression=select_expr,
        )

    func_name, col = match.groups()

    if func_name not in AGGREGATE_FUNCS:
        raise QueryError(
            f"Unknown aggregate function '{func_name}' in group context",
            error_type="UnknownFunction",
            step="select",
            expression=select_expr,
        )

    if col not in df.columns:
        available = ", ".join(sorted(df.columns))
        raise QueryError(
            f"Column '{col}' not found. Available: {available}",
            error_type="ValidationError",
            step="select",
            expression=select_expr,
        )

    return col_name, groups[col].agg(AGGREGATE_FUNCS[func_name])


def _aggregate_col_name(expr: str) -> str:
    """Generate column name from aggregate expression: mean(range) → mean_range."""
    expr = expr.strip()
    if expr == "count()":
        return "count"
    match = re.match(r"(\w+)\((\w+)(?:,\s*\w+)?\)", expr)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    return expr


def sort_df(df: pd.DataFrame, sort: str) -> pd.DataFrame:
    """Step 8: Sort result."""
    parts = sort.split()
    col = parts[0]
    ascending = len(parts) < 2 or parts[1].lower() != "desc"

    # After group_by, the group column becomes the index
    index_names = [n for n in df.index.names if n is not None]
    if col in index_names:
        return df.sort_index(ascending=ascending)
    if col in df.columns:
        return df.sort_values(col, ascending=ascending)

    available = ", ".join(sorted(list(df.columns) + index_names))
    raise QueryError(
        f"Sort column '{col}' not found. Available: {available}",
        error_type="ValidationError",
        step="sort",
        expression=sort,
    )


def _prepare_for_output(df: pd.DataFrame, query: dict) -> pd.DataFrame:
    """Prepare DataFrame for JSON output: split timestamp, order columns.

    Column order priority:
      1. date (always first)
      2. time (only for intraday timeframes)
      3. group_by keys (if grouped)
      4. OHLC columns (open, high, low, close)
      5. volume
      6. calculated columns (from map, in declaration order)
      7. any remaining columns
    """
    df = df.reset_index()

    # Split timestamp into date + time based on timeframe
    timeframe = query.get("from", "1m")
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
        df["date"] = ts.dt.strftime("%Y-%m-%d")
        if timeframe in _INTRADAY_TIMEFRAMES:
            df["time"] = ts.dt.strftime("%H:%M")
        df = df.drop(columns=["timestamp"])

    # Build ordered column list
    map_columns = list(query.get("map", {}).keys())
    group_by = query.get("group_by")
    group_cols = [group_by] if isinstance(group_by, str) else (group_by or [])

    ordered = []

    # 1. date
    if "date" in df.columns:
        ordered.append("date")

    # 2. time (if intraday)
    if "time" in df.columns:
        ordered.append("time")

    # 3. group keys
    for col in group_cols:
        if col in df.columns and col not in ordered:
            ordered.append(col)

    # 4. OHLC
    for col in _OHLC_COLUMNS:
        if col in df.columns:
            ordered.append(col)

    # 5. volume
    if "volume" in df.columns:
        ordered.append("volume")

    # 6. calculated columns (from map)
    for col in map_columns:
        if col in df.columns and col not in ordered:
            ordered.append(col)

    # 7. remaining columns
    for col in df.columns:
        if col not in ordered:
            ordered.append(col)

    return df[ordered]


def _serialize_records(records: list[dict]) -> list[dict]:
    """Convert DataFrame records to JSON-serializable format.

    Rounds calculated float values to CALCULATED_PRECISION, preserves OHLCV precision.
    """
    result = []
    for record in records:
        row = {}
        for key, value in record.items():
            if pd.isna(value):
                row[key] = None
            elif isinstance(value, pd.Timestamp):
                row[key] = value.isoformat()
            elif hasattr(value, "item"):  # numpy types
                v = value.item()
                if key in _PRESERVE_PRECISION or not isinstance(v, float):
                    row[key] = v
                else:
                    row[key] = round(v, CALCULATED_PRECISION)
            elif isinstance(value, float):
                if key in _PRESERVE_PRECISION:
                    row[key] = value
                else:
                    row[key] = round(value, CALCULATED_PRECISION)
            else:
                row[key] = value
        result.append(row)
    return result


def _build_response(result, query, rows, session, timeframe, warnings, source_df=None) -> dict:
    """Build the structured response with summary for model and table for UI."""
    metadata = {
        "rows": rows,
        "session": session,
        "from": timeframe,
        "warnings": warnings,
    }

    # Determine which columns to include in stats and first/last
    map_columns = list(query.get("map", {}).keys())
    sort_col = query.get("sort", "").split()[0] if query.get("sort") else None
    summary_columns = set(map_columns)
    if sort_col:
        summary_columns.add(sort_col)

    # Source rows: evidence for aggregated results (scalar/dict only)
    source_rows = None
    source_row_count = None
    has_aggregation = query.get("select") is not None

    is_valid_source = source_df is not None and isinstance(source_df, pd.DataFrame)
    if has_aggregation and is_valid_source and not source_df.empty:
        source_row_count = len(source_df)
        prepared = _prepare_for_output(source_df, query)
        source_rows = _serialize_records(prepared.to_dict("records"))

    # DataFrame result (table or grouped)
    if isinstance(result, pd.DataFrame):
        prepared = _prepare_for_output(result, query)
        table = _serialize_records(prepared.to_dict("records"))
        is_grouped = query.get("group_by") is not None

        summary = _build_summary_for_table(
            result,
            table,
            query,
            summary_columns,
            map_columns,
            is_grouped,
        )

        # Chart hint for grouped results
        chart = None
        if is_grouped:
            group_by = query.get("group_by")
            category = group_by if isinstance(group_by, str) else group_by[0]
            # Value columns = all columns except group_by key(s)
            group_keys = {group_by} if isinstance(group_by, str) else set(group_by)
            value_cols = [c for c in result.columns if c not in group_keys]
            if value_cols:
                chart = {"category": category, "value": value_cols[0]}

        return {
            "summary": summary,
            "table": table,
            "source_rows": source_rows,
            "source_row_count": source_row_count,
            "metadata": metadata,
            "query": query,
            "chart": chart,
        }

    # Dict result (multiple aggregates)
    if isinstance(result, dict):
        summary = {
            "type": "dict",
            "values": result,
            "rows_scanned": source_row_count or rows,
        }
        return {
            "summary": summary,
            "table": None,
            "source_rows": source_rows,
            "source_row_count": source_row_count,
            "metadata": metadata,
            "query": query,
        }

    # Scalar result
    if hasattr(result, "item"):
        result = result.item()

    summary = {
        "type": "scalar",
        "value": result,
        "rows_scanned": source_row_count or rows,
    }
    return {
        "summary": summary,
        "table": None,
        "source_rows": source_rows,
        "source_row_count": source_row_count,
        "metadata": metadata,
        "query": query,
    }


def _build_summary_for_table(
    df: pd.DataFrame,
    table: list,
    query: dict,
    summary_columns: set,
    map_columns: list,
    is_grouped: bool,
) -> dict:
    """Build summary metadata for table results."""
    summary = {
        "type": "grouped" if is_grouped else "table",
        "rows": len(table),
        "columns": list(df.columns),
    }

    if is_grouped:
        group_by = query.get("group_by")
        summary["by"] = group_by if isinstance(group_by, str) else group_by[0]

    # Stats for numeric columns in summary_columns
    stats = {}
    for col in summary_columns:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            stats[col] = {
                "min": float(df[col].min()) if not df[col].isna().all() else None,
                "max": float(df[col].max()) if not df[col].isna().all() else None,
                "mean": float(df[col].mean()) if not df[col].isna().all() else None,
            }
    if stats:
        summary["stats"] = stats

    # First/last rows with timestamp + map columns
    if table:
        first_last_cols = ["timestamp"] + map_columns
        # Filter to columns that exist
        first_last_cols = [c for c in first_last_cols if c in table[0]]

        first_row = {k: table[0].get(k) for k in first_last_cols if k in table[0]}
        last_row = {k: table[-1].get(k) for k in first_last_cols if k in table[-1]}

        # Convert timestamps to string for JSON
        for row in [first_row, last_row]:
            if "timestamp" in row and hasattr(row["timestamp"], "isoformat"):
                row["timestamp"] = row["timestamp"].isoformat()

        if first_row:
            summary["first"] = first_row
        if last_row and len(table) > 1:
            summary["last"] = last_row

    # For grouped: find min/max rows by first aggregate column
    if is_grouped and table:
        agg_cols = [c for c in df.columns if c not in (query.get("group_by") or [])]
        if agg_cols:
            agg_col = agg_cols[0]
            if pd.api.types.is_numeric_dtype(df[agg_col]):
                min_idx = df[agg_col].idxmin()
                max_idx = df[agg_col].idxmax()
                summary["min_row"] = {summary["by"]: min_idx, agg_col: float(df[agg_col].min())}
                summary["max_row"] = {summary["by"]: max_idx, agg_col: float(df[agg_col].max())}

    return summary
