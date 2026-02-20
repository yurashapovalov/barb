"""Tests for expression pre-validation.

Pre-validation catches syntax errors, unknown functions, and bad operators
across ALL query fields at once, before pipeline execution.
"""

import pytest

from barb.validation import ValidationError, validate_expressions


class TestSyntaxErrors:
    def test_lone_equals_in_where(self):
        """= instead of == is the most common LLM mistake."""
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions({"where": "close = open"})
        errors = exc_info.value.errors
        assert len(errors) == 1
        assert "==" in errors[0]["message"]
        assert errors[0]["step"] == "where"

    def test_lone_equals_in_map(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions({"map": {"flag": "close = open"}})
        assert "==" in exc_info.value.errors[0]["message"]

    def test_multiple_lone_equals(self):
        """Multiple = errors across fields are all caught."""
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions(
                {
                    "map": {"flag": "close = open"},
                    "where": "volume = 1000",
                }
            )
        assert len(exc_info.value.errors) == 2

    def test_unbalanced_parens(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions({"where": "(close > open"})
        assert "Syntax error" in exc_info.value.errors[0]["message"]

    def test_valid_equals_not_flagged(self):
        """==, !=, <=, >= must NOT trigger the lone = check."""
        validate_expressions({"where": "close == open"})
        validate_expressions({"where": "close != open"})
        validate_expressions({"where": "close <= open"})
        validate_expressions({"where": "close >= open"})


class TestUnknownFunctions:
    def test_unknown_function_in_map(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions({"map": {"x": "bogus(close)"}})
        assert "Unknown function 'bogus'" in exc_info.value.errors[0]["message"]

    def test_known_function_passes(self):
        validate_expressions({"map": {"x": "abs(close)"}})

    def test_if_function_passes(self):
        """'if' is a Python keyword but valid Barb function."""
        validate_expressions({"map": {"x": "if(close > open, 1, 0)"}})


class TestUnsupportedOperators:
    def test_unsupported_binary_op(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions({"map": {"x": "close ** 2"}})
        assert "Unsupported operator" in exc_info.value.errors[0]["message"]


class TestGroupByValidation:
    def test_function_call_in_group_by(self):
        """group_by: 'dayofweek()' is a common mistake — should use map first."""
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions({"group_by": "dayofweek()", "select": "count()"})
        errors = exc_info.value.errors
        assert "column name" in errors[0]["message"]
        assert "hint" in errors[0]

    def test_plain_column_name_passes(self):
        validate_expressions({"group_by": "weekday", "select": "count()"})

    def test_list_group_by_with_function(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions({"group_by": ["dayofweek()", "hour()"], "select": "count()"})
        assert len(exc_info.value.errors) == 2


class TestGroupSelectValidation:
    def test_unknown_aggregate_function(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions(
                {
                    "group_by": "weekday",
                    "select": "bogus(close)",
                }
            )
        assert "Unknown aggregate function" in exc_info.value.errors[0]["message"]

    def test_valid_aggregate_passes(self):
        validate_expressions(
            {
                "group_by": "weekday",
                "select": "mean(range)",
            }
        )

    def test_count_passes(self):
        validate_expressions(
            {
                "group_by": "weekday",
                "select": "count()",
            }
        )

    def test_comma_separated_select(self):
        validate_expressions(
            {
                "group_by": "weekday",
                "select": "mean(high), mean(low)",
            }
        )

    def test_comma_separated_with_error(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions(
                {
                    "group_by": "weekday",
                    "select": "mean(high), bogus(low)",
                }
            )
        assert len(exc_info.value.errors) == 1
        assert "bogus" in exc_info.value.errors[0]["message"]


class TestMultipleErrors:
    def test_errors_across_all_fields(self):
        """All errors from map, where, group_by collected at once."""
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions(
                {
                    "map": {"x": "close = open", "y": "bogus(close)"},
                    "where": "volume = 1000",
                    "group_by": "dayofweek()",
                    "select": "count()",
                }
            )
        errors = exc_info.value.errors
        assert len(errors) >= 4

    def test_error_count_in_message(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions(
                {
                    "map": {"x": "close = open"},
                    "where": "volume = 1000",
                }
            )
        assert "2 expression error(s)" in str(exc_info.value)


class TestValidQueriesPass:
    def test_empty_query(self):
        validate_expressions({})

    def test_full_valid_query(self):
        validate_expressions(
            {
                "map": {"range": "high - low", "weekday": "dayofweek()"},
                "where": "close > open and volume > 1000",
                "group_by": "weekday",
                "select": "mean(range)",
            }
        )

    def test_complex_expressions(self):
        validate_expressions(
            {
                "map": {
                    "gap": "open - prev(close)",
                    "range": "high - low",
                    "nr7": "rolling_min(range, 7)",
                },
                "where": "range == nr7 and gap != 0",
            }
        )

    def test_modulo_and_floordiv(self):
        validate_expressions({"map": {"bucket": "minute() % 10", "hr": "minute() // 60"}})

    def test_select_without_group_by(self):
        validate_expressions({"select": "mean(close)"})

    def test_where_with_in_operator(self):
        validate_expressions({"where": "dayofweek() in [0, 1, 2]"})

    def test_where_with_not(self):
        validate_expressions({"where": "not (close > open)"})

    def test_map_non_string_value(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_expressions({"map": {"x": 42}})
        assert "must be a string expression" in exc_info.value.errors[0]["message"]
