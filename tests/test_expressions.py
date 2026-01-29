"""Tests for the expression parser and evaluator."""

import numpy as np
import pandas as pd
import pytest

from barb.expressions import evaluate, ExpressionError
from barb.functions import FUNCTIONS


@pytest.fixture
def df():
    """Small DataFrame with known values for expression tests."""
    return pd.DataFrame({
        "open": [100.0, 102.0, 101.0, 105.0, 103.0],
        "high": [105.0, 106.0, 104.0, 108.0, 107.0],
        "low": [98.0, 100.0, 99.0, 103.0, 101.0],
        "close": [103.0, 101.0, 103.0, 106.0, 104.0],
        "volume": [1000, 1500, 1200, 2000, 800],
    })


@pytest.fixture
def functions():
    """Minimal functions for testing expression evaluation."""
    return {
        "abs": lambda df, x: x.abs() if isinstance(x, pd.Series) else abs(x),
        "prev": lambda df, col, n=1: col.shift(int(n)),
        "if": FUNCTIONS["if"],
    }


# --- Arithmetic ---

class TestArithmetic:
    def test_subtraction(self, df, functions):
        result = evaluate("high - low", df, functions)
        assert list(result) == [7.0, 6.0, 5.0, 5.0, 6.0]

    def test_addition(self, df, functions):
        result = evaluate("open + close", df, functions)
        assert list(result) == [203.0, 203.0, 204.0, 211.0, 207.0]

    def test_multiplication(self, df, functions):
        result = evaluate("close * volume", df, functions)
        assert list(result) == [103000.0, 151500.0, 123600.0, 212000.0, 83200.0]

    def test_division(self, df, functions):
        range_vals = evaluate("(high - low) / close", df, functions)
        # range / close for first row: 7.0 / 103.0
        assert abs(range_vals.iloc[0] - 7.0 / 103.0) < 1e-10

    def test_literal_arithmetic(self, df, functions):
        result = evaluate("close * 2", df, functions)
        assert list(result) == [206.0, 202.0, 206.0, 212.0, 208.0]

    def test_parentheses(self, df, functions):
        result = evaluate("(close - open) / (high - low)", df, functions)
        # First row: (103-100)/(105-98) = 3/7
        assert abs(result.iloc[0] - 3.0 / 7.0) < 1e-10

    def test_unary_minus(self, df, functions):
        result = evaluate("-close", df, functions)
        assert list(result) == [-103.0, -101.0, -103.0, -106.0, -104.0]


# --- Comparisons ---

class TestComparisons:
    def test_greater_than(self, df, functions):
        result = evaluate("close > open", df, functions)
        assert list(result) == [True, False, True, True, True]

    def test_less_than(self, df, functions):
        result = evaluate("close < 104", df, functions)
        assert list(result) == [True, True, True, False, False]

    def test_equal(self, df, functions):
        result = evaluate("volume == 1500", df, functions)
        assert list(result) == [False, True, False, False, False]

    def test_not_equal(self, df, functions):
        result = evaluate("volume != 1000", df, functions)
        assert list(result) == [False, True, True, True, True]

    def test_greater_equal(self, df, functions):
        result = evaluate("close >= 103", df, functions)
        assert list(result) == [True, False, True, True, True]

    def test_less_equal(self, df, functions):
        result = evaluate("volume <= 1000", df, functions)
        assert list(result) == [True, False, False, False, True]


# --- Boolean Logic ---

class TestBooleanLogic:
    def test_and(self, df, functions):
        result = evaluate("close > open and volume > 1000", df, functions)
        # close > open: [T, F, T, T, T], volume > 1000: [F, T, T, T, F]
        assert list(result) == [False, False, True, True, False]

    def test_or(self, df, functions):
        result = evaluate("volume == 1000 or volume == 2000", df, functions)
        assert list(result) == [True, False, False, True, False]

    def test_not(self, df, functions):
        result = evaluate("not (close > open)", df, functions)
        assert list(result) == [False, True, False, False, False]


# --- Membership ---

class TestMembership:
    def test_in_list(self, df, functions):
        df_with_weekday = df.copy()
        df_with_weekday["weekday"] = [0, 1, 2, 3, 4]
        result = evaluate("weekday in [0, 4]", df_with_weekday, functions)
        assert list(result) == [True, False, False, False, True]


# --- Function Calls ---

class TestFunctionCalls:
    def test_abs(self, df, functions):
        result = evaluate("abs(close - open)", df, functions)
        # close - open: [3, -1, 2, 1, 1]
        assert list(result) == [3.0, 1.0, 2.0, 1.0, 1.0]

    def test_prev(self, df, functions):
        result = evaluate("prev(close)", df, functions)
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] == 103.0
        assert result.iloc[2] == 101.0

    def test_nested_expression_in_function(self, df, functions):
        result = evaluate("abs(open - close)", df, functions)
        assert list(result) == [3.0, 1.0, 2.0, 1.0, 1.0]

    def test_if_function(self, df, functions):
        """if() is a Python keyword but works as a Barb function."""
        result = evaluate("if(close > open, 1, 0)", df, functions)
        # close > open: [T, F, T, T, T]
        assert list(result) == [1, 0, 1, 1, 1]

    def test_if_nested_in_expression(self, df, functions):
        """if() inside arithmetic expression."""
        result = evaluate("if(close > open, 1, 0) + if(volume > 1000, 1, 0)", df, functions)
        # close>open: [T,F,T,T,T], vol>1000: [F,T,T,T,F]
        assert list(result) == [1, 1, 2, 2, 1]


# --- Error Handling ---

class TestErrors:
    def test_unknown_column(self, df, functions):
        with pytest.raises(ExpressionError, match="Unknown column 'foo'"):
            evaluate("foo + bar", df, functions)

    def test_unknown_function(self, df, functions):
        with pytest.raises(ExpressionError, match="Unknown function 'bogus'"):
            evaluate("bogus(close)", df, functions)

    def test_parse_error(self, df, functions):
        with pytest.raises(ExpressionError, match="Parse error"):
            evaluate("close +", df, functions)

    def test_method_call_rejected(self, df, functions):
        with pytest.raises(ExpressionError, match="Only simple function calls"):
            evaluate("close.mean()", df, functions)
