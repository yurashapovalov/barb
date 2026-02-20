"""Barb Script interpreter.

Executes a JSON query against a pandas DataFrame.
Single-step pipeline: session → period → from → map → where → group_by → select → sort → limit
Multi-step (steps): each step's output is the next step's input.
"""

import datetime
import re

import pandas as pd

from barb.expressions import ExpressionError, evaluate
from barb.functions import AGGREGATE_FUNCS, FUNCTIONS
from barb.ops import (
    INTRADAY_TIMEFRAMES,
    TIMEFRAMES,
    BarbError,
    add_session_id,
    filter_period,
    filter_session,
    resample,
)
from barb.validation import validate_expressions

# Standard OHLC column order
_OHLC_COLUMNS = ["open", "high", "low", "close"]

# Auto-format time functions for display.
# Filtering uses numbers; output shows readable labels.
_DAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}
_MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}
DISPLAY_FORMATS = {
    "dayofweek()": lambda v: v.map(_DAY_NAMES),
    "month()": lambda v: v.map(_MONTH_NAMES),
    "hour()": lambda v: v.map(lambda h: f"{int(h):02d}:00-{int(h):02d}:59"),
}

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
    "columns",
    "steps",
}


def execute(query: dict, df: pd.DataFrame, sessions: dict) -> dict:
    """Execute a Barb Script query.

    Args:
        query: JSON query dict (flat or with steps)
        df: DataFrame with DatetimeIndex and OHLCV columns (daily or minute)
        sessions: {"RTH": ("09:30", "17:00"), ...}

    Returns:
        {"summary": ..., "table": [...] | None, "source_rows": ...,
         "source_row_count": ..., "metadata": {...}, "query": query, "chart": ...}

    Raises:
        BarbError: On validation or execution failure
    """
    _validate(query)

    if "steps" in query:
        return _execute_steps(query, df, sessions)

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

    # 3.5. SESSION BOUNDARIES — for session_high/low/open/close
    if session_name and session_name.upper() in sessions:
        df = add_session_id(df, sessions[session_name.upper()])

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


def _execute_steps(query: dict, df: pd.DataFrame, sessions: dict) -> dict:
    """Execute a multi-step query. Each step's output feeds the next."""
    steps = query["steps"]
    if not isinstance(steps, list) or len(steps) == 0:
        raise BarbError(
            "steps must be a non-empty array",
            error_type="ValidationError",
            step="validate",
        )

    warnings = []
    timeframe = "1m"
    session_name = None

    for i, step in enumerate(steps):
        # Step 1: scope data (session → period → from)
        if i == 0:
            session_name = step.get("session")
            timeframe = step.get("from", "1m")

            if session_name:
                has_time = hasattr(df.index, "hour") and (df.index.hour != 0).any()
                if has_time:
                    df, warn = filter_session(df, session_name, sessions)
                    if warn:
                        warnings.append(warn)

            period = step.get("period")
            if period:
                df = filter_period(df, period)

            df = resample(df, timeframe)

            # Session boundaries for session_high/low/open/close
            if session_name and session_name.upper() in sessions:
                df = add_session_id(df, sessions[session_name.upper()])

        # All steps: map → where
        if step.get("map"):
            df = compute_map(df, step["map"])
        if step.get("where"):
            df = filter_where(df, step["where"])

        # Intermediate steps: group_by → select (output feeds next step)
        is_last = i == len(steps) - 1
        if not is_last:
            group_by = step.get("group_by")
            select_raw = step.get("select")
            if group_by:
                select = _normalize_select(select_raw or "count()")
                df = _group_aggregate(df, group_by, select)
                df = df.reset_index()

    # Finalize with last step: group_by → select → sort → limit
    last = steps[-1]
    rows_after_filter = len(df)
    source_df = df

    group_by = last.get("group_by")
    select_raw = last.get("select")

    if group_by:
        select = _normalize_select(select_raw or "count()")
        result_df = _group_aggregate(df, group_by, select)
    elif select_raw:
        select = _normalize_select(select_raw)
        result_df = _aggregate(df, select)
    else:
        result_df = df

    if last.get("sort") and isinstance(result_df, pd.DataFrame):
        result_df = sort_df(result_df, last["sort"])

    if last.get("limit") and isinstance(result_df, pd.DataFrame):
        result_df = result_df.head(last["limit"])

    # Build virtual query for response formatting
    all_maps = {}
    for step in steps:
        all_maps.update(step.get("map", {}))

    virtual_query = {"from": timeframe, "map": all_maps}
    if query.get("columns"):
        virtual_query["columns"] = query["columns"]
    for field in ("group_by", "select", "sort", "limit"):
        if field in last:
            virtual_query[field] = last[field]

    return _build_response(
        result_df,
        virtual_query,
        rows_after_filter,
        session_name,
        timeframe,
        warnings,
        source_df,
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
        raise BarbError(
            f"Unknown fields: {', '.join(unknown)}. Valid: {', '.join(sorted(_VALID_FIELDS))}",
            error_type="ValidationError",
            step="validate",
        )

    tf = query.get("from", "1m")
    if tf not in TIMEFRAMES:
        raise BarbError(
            f"Invalid timeframe '{tf}'. Valid: {', '.join(sorted(TIMEFRAMES))}",
            error_type="ValidationError",
            step="validate",
        )

    if "limit" in query and (not isinstance(query["limit"], int) or query["limit"] < 1):
        raise BarbError(
            "limit must be a positive integer",
            error_type="ValidationError",
            step="validate",
        )

    if "map" in query and not isinstance(query["map"], dict):
        raise BarbError(
            "map must be an object {name: expression}",
            error_type="ValidationError",
            step="validate",
        )


# --- Pipeline steps (session, period, resample are in barb/ops.py) ---


def compute_map(df: pd.DataFrame, map_config: dict) -> pd.DataFrame:
    """Step 4: Compute derived columns in declaration order."""
    df = df.copy()
    for name, expr in map_config.items():
        if not isinstance(expr, str):
            raise BarbError(
                f"map value for '{name}' must be a string expression, got {type(expr).__name__}",
                error_type="TypeError",
                step="map",
                expression=str(expr),
            )
        try:
            df[name] = evaluate(expr, df, FUNCTIONS)
        except ExpressionError as e:
            raise BarbError(
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
        raise BarbError(
            str(e),
            error_type="ExpressionError",
            step="where",
            expression=where_expr,
        ) from e

    if not isinstance(mask, pd.Series):
        raise BarbError(
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
            raise BarbError(
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
            raise BarbError(
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
            raise BarbError(
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
        raise BarbError(
            f"Cannot parse aggregate expression: '{select_expr}'",
            error_type="ParseError",
            step="select",
            expression=select_expr,
        )

    func_name, col = match.groups()

    if func_name not in AGGREGATE_FUNCS:
        raise BarbError(
            f"Unknown aggregate function '{func_name}' in group context",
            error_type="UnknownFunction",
            step="select",
            expression=select_expr,
        )

    if col not in df.columns:
        available = ", ".join(sorted(df.columns))
        raise BarbError(
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

    # "date" is created later in _prepare_for_output(); alias to timestamp
    if col == "date" and ("timestamp" in df.columns or "timestamp" in index_names):
        col = "timestamp"
    if col in index_names:
        return df.sort_index(ascending=ascending)
    if col in df.columns:
        return df.sort_values(col, ascending=ascending)

    available = ", ".join(sorted(list(df.columns) + index_names))
    raise BarbError(
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
      4. calculated columns (from map, in declaration order)
      5. OHLC columns (open, high, low, close)
      6. volume
      7. any remaining columns

    Map columns before OHLC: derived data is more relevant than raw candles.
    """
    df = df.reset_index()

    # Drop internal columns (e.g. __session_id)
    internal = [c for c in df.columns if c.startswith("__")]
    if internal:
        df = df.drop(columns=internal)

    # Split timestamp into date + time based on timeframe
    timeframe = query.get("from", "1m")
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
        df["date"] = ts.dt.strftime("%Y-%m-%d")
        if timeframe in INTRADAY_TIMEFRAMES:
            df["time"] = ts.dt.strftime("%H:%M")
        df = df.drop(columns=["timestamp"])

    # Projection: model controls which columns to show
    columns = query.get("columns")
    if columns:
        cols = [c for c in columns if c in df.columns]
        if cols:
            return df[cols]

    # Fallback: model didn't send columns — current ordering logic
    map_columns = list(query.get("map", {}).keys())
    group_by = query.get("group_by")
    group_cols = [group_by] if isinstance(group_by, str) else (group_by or [])

    ordered = []

    if "date" in df.columns:
        ordered.append("date")
    if "time" in df.columns:
        ordered.append("time")
    for col in group_cols:
        if col in df.columns and col not in ordered:
            ordered.append(col)
    for col in map_columns:
        if col in df.columns and col not in ordered:
            ordered.append(col)
    for col in _OHLC_COLUMNS:
        if col in df.columns:
            ordered.append(col)
    if "volume" in df.columns:
        ordered.append("volume")
    for col in df.columns:
        if col not in ordered:
            ordered.append(col)

    df = df[ordered]

    # Auto-format time columns for display (dayofweek→Monday, month→January, hour→09:00-09:59)
    map_exprs = query.get("map", {})
    for col_name, expr in map_exprs.items():
        fmt = DISPLAY_FORMATS.get(expr)
        if fmt and col_name in df.columns:
            df[col_name] = fmt(df[col_name])

    return df


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
            elif isinstance(value, datetime.date):
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
    table: list,
    query: dict,
    summary_columns: set,
    map_columns: list,
    is_grouped: bool,
) -> dict:
    """Build summary metadata from the formatted table (what the user sees)."""
    summary = {
        "type": "grouped" if is_grouped else "table",
        "rows": len(table),
    }

    if is_grouped:
        group_by = query.get("group_by")
        summary["by"] = group_by if isinstance(group_by, str) else group_by[0]

    # Stats for numeric columns in summary_columns
    if table:
        stats = {}
        for col in summary_columns:
            if col not in table[0]:
                continue
            vals = [r[col] for r in table if isinstance(r.get(col), (int, float))]
            if vals:
                stats[col] = {
                    "min": min(vals),
                    "max": max(vals),
                    "mean": round(sum(vals) / len(vals), 2),
                }
        if stats:
            summary["stats"] = stats

    # First/last rows with date/time + map columns
    if table:
        first_last_cols = ["date", "time"] + map_columns
        first_last_cols = [c for c in first_last_cols if c in table[0]]

        first_row = {k: table[0][k] for k in first_last_cols if k in table[0]}
        last_row = {k: table[-1][k] for k in first_last_cols if k in table[-1]}

        if first_row:
            summary["first"] = first_row
        if last_row and len(table) > 1:
            summary["last"] = last_row

    # For grouped: find min/max rows by first aggregate column
    if is_grouped and table:
        group_by = query.get("group_by")
        group_keys = [group_by] if isinstance(group_by, str) else (group_by or [])
        agg_cols = [c for c in table[0] if c not in group_keys]
        if agg_cols:
            agg_col = agg_cols[0]
            numeric_rows = [r for r in table if isinstance(r.get(agg_col), (int, float))]
            if numeric_rows:
                min_row = min(numeric_rows, key=lambda r: r[agg_col])
                max_row = max(numeric_rows, key=lambda r: r[agg_col])
                keys = group_keys + [agg_col]
                summary["min_row"] = {k: min_row[k] for k in keys if k in min_row}
                summary["max_row"] = {k: max_row[k] for k in keys if k in max_row}

    return summary
