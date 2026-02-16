"""Integration tests for the Barb Script interpreter.

Uses real NQ data (fixed slice 2024-01-01 to 2024-06-30).
Tests the full pipeline: query → execute → result.
"""

import pytest

from barb.interpreter import QueryError, execute
from barb.validation import ValidationError

# --- Validation ---


class TestValidation:
    def test_unknown_field(self, nq_minute_slice, sessions):
        with pytest.raises(QueryError, match="Unknown fields"):
            execute({"foo": "bar"}, nq_minute_slice, sessions)

    def test_invalid_timeframe(self, nq_minute_slice, sessions):
        with pytest.raises(QueryError, match="Invalid timeframe"):
            execute({"from": "3m"}, nq_minute_slice, sessions)

    def test_invalid_limit(self, nq_minute_slice, sessions):
        with pytest.raises(QueryError, match="limit must be"):
            execute({"from": "daily", "limit": -1}, nq_minute_slice, sessions)

    def test_empty_query(self, nq_minute_slice, sessions):
        """Empty query returns all rows."""
        result = execute({}, nq_minute_slice, sessions)
        assert isinstance(result["table"], list)
        assert len(result["table"]) > 0

    def test_expression_errors_caught_before_execution(self, nq_minute_slice, sessions):
        """Pre-validation catches all expression errors at once."""
        with pytest.raises(ValidationError) as exc_info:
            execute(
                {
                    "from": "daily",
                    "map": {"x": "close = open", "y": "bogus(high)"},
                    "where": "volume = 1000",
                },
                nq_minute_slice,
                sessions,
            )
        assert len(exc_info.value.errors) == 3


# --- Session Filtering ---


class TestSession:
    def test_rth_filter(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        all_result = execute({"select": "count()"}, nq_minute_slice, sessions)
        # RTH should have fewer bars than all data
        assert result["summary"]["value"] < all_result["summary"]["value"]

    def test_unknown_session_warning(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "BOGUS",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert any("Unknown session" in w for w in result["metadata"]["warnings"])


# --- Resample ---


class TestResample:
    def test_daily_resample(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        # ~125-155 trading days in 6 months (includes some Sunday evening bars)
        assert 100 < result["summary"]["value"] < 160

    def test_weekly_resample(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "weekly",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        # ~26 weeks in 6 months
        assert 20 < result["summary"]["value"] < 30


# --- Map ---


class TestMap:
    def test_range(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"range": "high - low"},
                "select": "mean(range)",
            },
            nq_minute_slice,
            sessions,
        )
        # NQ daily range should be positive and reasonable
        assert 30 < result["summary"]["value"] < 300

    def test_map_ordering(self, nq_minute_slice, sessions):
        """Later map columns can reference earlier ones."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {
                    "range": "high - low",
                    "half_range": "range / 2",
                },
                "select": "mean(half_range)",
            },
            nq_minute_slice,
            sessions,
        )
        # half_range should be positive
        assert result["summary"]["value"] > 0


# --- Where ---


class TestWhere:
    def test_filter_bullish_days(self, nq_minute_slice, sessions):
        all_days = execute(
            {
                "session": "RTH",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )

        bullish = execute(
            {
                "session": "RTH",
                "from": "daily",
                "where": "close > open",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )

        # Some days are bullish, but not all
        assert 0 < bullish["summary"]["value"] < all_days["summary"]["value"]

    def test_inside_day(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "where": "high < prev(high) and low > prev(low)",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert result["summary"]["value"] >= 0


# --- Normalization ---


class TestNormalization:
    def test_comma_separated_select(self, nq_minute_slice, sessions):
        """'mean(high), mean(low)' as one string is split and both computed."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"weekday": "dayofweek()"},
                "group_by": "weekday",
                "select": "mean(high), mean(low)",
            },
            nq_minute_slice,
            sessions,
        )
        assert len(result["table"]) == 5
        assert "mean_high" in result["table"][0]
        assert "mean_low" in result["table"][0]

    def test_single_select_unchanged(self, nq_minute_slice, sessions):
        """Single select without comma works as before."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert isinstance(result["summary"]["value"], (int, float))


# --- Group By ---


class TestGroupBy:
    def test_volume_by_weekday(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"weekday": "dayofweek()"},
                "group_by": "weekday",
                "select": "mean(volume)",
                "sort": "weekday asc",
            },
            nq_minute_slice,
            sessions,
        )
        # 5 weekdays (0-4, no weekends in RTH data)
        assert len(result["table"]) == 5

    def test_group_by_missing_column(self, nq_minute_slice, sessions):
        """group_by on non-existent column gives clear error."""
        with pytest.raises(QueryError, match="Column 'bogus' not found") as exc_info:
            execute(
                {
                    "session": "RTH",
                    "from": "daily",
                    "group_by": "bogus",
                    "select": "count()",
                },
                nq_minute_slice,
                sessions,
            )
        assert exc_info.value.step == "group_by"

    def test_select_missing_column(self, nq_minute_slice, sessions):
        """select aggregate on non-existent column gives clear error."""
        with pytest.raises(QueryError, match="Column 'bogus' not found") as exc_info:
            execute(
                {
                    "session": "RTH",
                    "from": "daily",
                    "map": {"weekday": "dayofweek()"},
                    "group_by": "weekday",
                    "select": "mean(bogus)",
                },
                nq_minute_slice,
                sessions,
            )
        assert exc_info.value.step == "select"

    def test_group_with_count(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"weekday": "dayofweek()"},
                "group_by": "weekday",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert len(result["table"]) == 5
        # Each weekday should have ~25 days in 6 months
        for row in result["table"]:
            assert row["count"] > 15


# --- Sort + Limit ---


class TestSortLimit:
    def test_sort_desc(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"range": "high - low", "weekday": "dayofweek()"},
                "group_by": "weekday",
                "select": "mean(range)",
                "sort": "mean_range desc",
            },
            nq_minute_slice,
            sessions,
        )
        rows = result["table"]
        # Check descending order
        for i in range(len(rows) - 1):
            assert rows[i]["mean_range"] >= rows[i + 1]["mean_range"]

    def test_limit(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"range": "high - low", "weekday": "dayofweek()"},
                "group_by": "weekday",
                "select": "mean(range)",
                "sort": "mean_range desc",
                "limit": 3,
            },
            nq_minute_slice,
            sessions,
        )
        assert len(result["table"]) == 3

    def test_sort_unknown_column(self, nq_minute_slice, sessions):
        """Sort on non-existent column gives clear error."""
        with pytest.raises(QueryError, match="Sort column 'bogus' not found") as exc_info:
            execute(
                {
                    "session": "RTH",
                    "from": "daily",
                    "map": {"weekday": "dayofweek()"},
                    "group_by": "weekday",
                    "select": "count()",
                    "sort": "bogus desc",
                },
                nq_minute_slice,
                sessions,
            )
        assert exc_info.value.step == "sort"

    def test_join_field_rejected(self, nq_minute_slice, sessions):
        """'join' is not a valid field (unimplemented)."""
        with pytest.raises(QueryError, match="Unknown fields"):
            execute({"join": "events", "from": "daily"}, nq_minute_slice, sessions)


# --- Period ---


class TestPeriod:
    def test_year_filter(self, nq_minute_slice, sessions):
        result = execute(
            {
                "period": "2024",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert result["summary"]["value"] > 0

    def test_month_filter(self, nq_minute_slice, sessions):
        result = execute(
            {
                "period": "2024-03",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        # March has ~21 weekdays + some Sundays (NQ trades Sunday evening)
        assert 15 < result["summary"]["value"] < 30

    def test_open_end_range(self, nq_minute_slice, sessions):
        """Open-ended range '2024-06:' means from June 2024 to end."""
        result = execute(
            {
                "period": "2024-06:",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        # June 2024 to end of data (June 30)
        assert result["summary"]["value"] > 0

    def test_month_range(self, nq_minute_slice, sessions):
        """Month range '2024-03:2024-04' filters by months."""
        result = execute(
            {
                "period": "2024-03:2024-04",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        # March + April ~ 40-50 days
        assert 30 < result["summary"]["value"] < 60

    def test_invalid_period_string(self, nq_minute_slice, sessions):
        """Invalid period like 'all' gives clear error, not internal crash."""
        with pytest.raises(QueryError, match="Invalid period 'all'") as exc_info:
            execute({"period": "all", "from": "daily"}, nq_minute_slice, sessions)
        assert exc_info.value.step == "period"

    def test_invalid_period_range(self, nq_minute_slice, sessions):
        with pytest.raises(QueryError, match="Invalid period start"):
            execute({"period": "start:end", "from": "daily"}, nq_minute_slice, sessions)

    def test_relative_period_last_month(self, nq_minute_slice, sessions):
        result = execute(
            {
                "period": "last_month",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert result["summary"]["value"] > 0


# --- Response Format ---


class TestResponse:
    def test_scalar_response(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert "summary" in result
        assert "metadata" in result
        assert "query" in result
        assert result["table"] is None  # scalar result
        assert isinstance(result["summary"]["value"], (int, float))

    def test_table_response(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"weekday": "dayofweek()"},
                "group_by": "weekday",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert result["table"] is not None
        assert isinstance(result["table"], list)
        assert len(result["table"]) > 0

    def test_metadata_fields(self, nq_minute_slice, sessions):
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        meta = result["metadata"]
        assert "rows" in meta
        assert meta["session"] == "RTH"
        assert meta["from"] == "daily"

    def test_error_response(self, nq_minute_slice, sessions):
        with pytest.raises(QueryError) as exc_info:
            execute(
                {
                    "from": "daily",
                    "map": {"bad": "nonexistent_column + 1"},
                },
                nq_minute_slice,
                sessions,
            )
        assert exc_info.value.step == "map"


# --- Full Examples from Spec ---


class TestSpecExamples:
    """Queries from the spec examples section."""

    def test_average_daily_range(self, nq_minute_slice, sessions):
        """Spec 13.1-like: average daily range."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"range": "high - low"},
                "select": "mean(range)",
            },
            nq_minute_slice,
            sessions,
        )
        # NQ daily RTH range should be reasonable
        assert 30 < result["summary"]["value"] < 300

    def test_gap_analysis(self, nq_minute_slice, sessions):
        """Spec 13.7-like: gap analysis."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"gap": "open - prev(close)"},
                "where": "gap != 0",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert result["summary"]["value"] > 0

    def test_nr7_count(self, nq_minute_slice, sessions):
        """Spec 13.9-like: NR7 days."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {
                    "range": "high - low",
                    "min_range_7": "rolling_min(range, 7)",
                },
                "where": "range == min_range_7",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert result["summary"]["value"] >= 0


# --- Source Rows (Evidence) ---


class TestSourceRows:
    def test_scalar_has_source_rows(self, nq_minute_slice, sessions):
        """count() with where returns source_rows matching the count."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "where": "close > open",
                "select": "count()",
            },
            nq_minute_slice,
            sessions,
        )
        assert isinstance(result["summary"]["value"], (int, float))
        assert result["source_rows"] is not None
        assert len(result["source_rows"]) == result["summary"]["value"]
        assert result["source_row_count"] == result["summary"]["value"]

    def test_mean_has_source_rows(self, nq_minute_slice, sessions):
        """mean() returns all filtered rows as source_rows."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"range": "high - low"},
                "select": "mean(range)",
            },
            nq_minute_slice,
            sessions,
        )
        assert result["source_rows"] is not None
        assert result["source_row_count"] > 0
        assert len(result["source_rows"]) == result["source_row_count"]

    def test_group_by_has_source_rows(self, nq_minute_slice, sessions):
        """group_by returns grouped table + pre-grouped source rows."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"weekday": "dayofweek()"},
                "group_by": "weekday",
                "select": "mean(close)",
            },
            nq_minute_slice,
            sessions,
        )
        assert result["table"] is not None
        assert result["source_rows"] is not None
        assert result["source_row_count"] > len(result["table"])

    def test_no_select_returns_table(self, nq_minute_slice, sessions):
        """Without select, table contains filtered rows directly."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "where": "close > open",
            },
            nq_minute_slice,
            sessions,
        )
        # No aggregation = no source_rows needed, table IS the result
        assert result["source_rows"] is None
        assert isinstance(result["table"], list)
        assert len(result["table"]) > 0

    def test_source_rows_have_columns(self, nq_minute_slice, sessions):
        """Source rows contain the columns available before aggregation."""
        result = execute(
            {
                "session": "RTH",
                "from": "daily",
                "map": {"range": "high - low"},
                "where": "close > open",
                "select": "mean(range)",
            },
            nq_minute_slice,
            sessions,
        )
        row = result["source_rows"][0]
        assert "open" in row
        assert "close" in row
        assert "range" in row


class TestSerialization:
    def test_date_function_serialized_to_string(self, nq_daily, sessions):
        """datetime.date objects from date() are serialized to ISO strings."""
        result = execute(
            {"from": "daily", "map": {"d": "date()"}, "limit": 3},
            nq_daily,
            sessions,
        )
        for row in result["table"]:
            assert isinstance(row["d"], str)
            assert len(row["d"]) == 10  # "YYYY-MM-DD"

    def test_column_order_preserved_in_table(self, nq_daily, sessions):
        """Table rows preserve column order: date, OHLCV, then map columns."""
        result = execute(
            {"from": "daily", "map": {"range": "high - low"}, "limit": 1},
            nq_daily,
            sessions,
        )
        keys = list(result["table"][0].keys())
        assert keys[0] == "date"
        assert keys[1:6] == ["open", "high", "low", "close", "volume"]
        assert keys[6] == "range"

    def test_column_order_intraday(self, nq_minute_slice, sessions):
        """Intraday results have date, time, then OHLCV."""
        result = execute(
            {"from": "1h", "period": "2024-01", "limit": 1},
            nq_minute_slice,
            sessions,
        )
        keys = list(result["table"][0].keys())
        assert keys[0] == "date"
        assert keys[1] == "time"

    def test_column_order_grouped(self, nq_daily, sessions):
        """Grouped results have group key first, then aggregates."""
        result = execute(
            {
                "from": "daily",
                "map": {"dow": "dayofweek()"},
                "group_by": "dow",
                "select": "mean(close)",
            },
            nq_daily,
            sessions,
        )
        keys = list(result["table"][0].keys())
        assert keys[0] == "dow"
