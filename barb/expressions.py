"""AST-based expression parser and evaluator for Barb Script.

Parses expression strings into Python AST, then evaluates against
a pandas DataFrame with a whitelist of allowed operations.
No arbitrary code execution — only approved node types and functions.
"""

import ast
import operator
import re

import pandas as pd


class ExpressionError(Exception):
    """Raised when an expression cannot be parsed or evaluated."""
    pass


# Python keywords used as Barb function names → safe aliases for ast.parse
_KEYWORD_ALIASES = {"if": "_barb_if_"}
_REVERSE_ALIASES = {v: k for k, v in _KEYWORD_ALIASES.items()}


def _preprocess_keywords(expr: str) -> str:
    """Replace keyword function names with safe aliases before ast.parse."""
    for kw, alias in _KEYWORD_ALIASES.items():
        expr = re.sub(rf'\b{kw}\s*\(', f'{alias}(', expr)
    return expr


# Operators mapped to pandas-compatible callables
_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_COMPARE_OPS = {
    ast.Gt: operator.gt,
    ast.Lt: operator.lt,
    ast.GtE: operator.ge,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


def evaluate(expr: str, df: pd.DataFrame, functions: dict) -> pd.Series | float | int | bool:
    """Parse and evaluate an expression string against a DataFrame.

    Args:
        expr: Expression string like "high - low" or "rolling_mean(close, 20)"
        df: DataFrame with columns available as variables
        functions: Dict of {name: callable} for function calls

    Returns:
        Series, scalar, or boolean result

    Raises:
        ExpressionError: On parse failure, unknown column, or disallowed operation
    """
    # Replace Python keywords used as Barb functions before parsing
    parsed_expr = _preprocess_keywords(expr)

    try:
        tree = ast.parse(parsed_expr, mode="eval")
    except SyntaxError as e:
        raise ExpressionError(f"Parse error in '{expr}': {e.msg}") from e

    return _eval_node(tree.body, df, functions)


def _eval_node(node: ast.AST, df: pd.DataFrame, functions: dict):
    """Recursively evaluate an AST node."""

    # Literal values: 42, 3.14, "text", True
    if isinstance(node, ast.Constant):
        return node.value

    # Column reference or boolean keyword: close, volume, true, false
    if isinstance(node, ast.Name):
        name = node.id
        if name == "true":
            return True
        if name == "false":
            return False
        if name in df.columns:
            return df[name]
        raise ExpressionError(
            f"Unknown column '{name}'. Available: {', '.join(df.columns)}"
        )

    # Arithmetic: high - low, close * volume
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, df, functions)
        right = _eval_node(node.right, df, functions)
        op_func = _BINARY_OPS.get(type(node.op))
        if op_func is None:
            raise ExpressionError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(left, right)

    # Unary: -close, not condition
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, df, functions)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.Not):
            return ~operand if isinstance(operand, pd.Series) else not operand
        raise ExpressionError(f"Unsupported unary operator: {type(node.op).__name__}")

    # Comparison: close > open, volume >= 1000, weekday in [0, 1]
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, df, functions)
        result = None
        current = left
        for op, comparator_node in zip(node.ops, node.comparators):
            if isinstance(op, ast.In):
                right = _eval_node(comparator_node, df, functions)
                if isinstance(current, pd.Series):
                    comparison = current.isin(right)
                else:
                    comparison = current in right
            elif isinstance(op, ast.NotIn):
                right = _eval_node(comparator_node, df, functions)
                if isinstance(current, pd.Series):
                    comparison = ~current.isin(right)
                else:
                    comparison = current not in right
            else:
                right = _eval_node(comparator_node, df, functions)
                op_func = _COMPARE_OPS.get(type(op))
                if op_func is None:
                    raise ExpressionError(f"Unsupported comparison: {type(op).__name__}")
                comparison = op_func(current, right)
            result = comparison if result is None else (result & comparison)
            current = right
        return result

    # Boolean logic: close > open and volume > 1000
    if isinstance(node, ast.BoolOp):
        values = [_eval_node(v, df, functions) for v in node.values]
        if isinstance(node.op, ast.And):
            result = values[0]
            for v in values[1:]:
                result = result & v
            return result
        if isinstance(node.op, ast.Or):
            result = values[0]
            for v in values[1:]:
                result = result | v
            return result
        raise ExpressionError(f"Unsupported boolean op: {type(node.op).__name__}")

    # Function call: abs(x), rolling_mean(close, 20), count()
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ExpressionError("Only simple function calls allowed (no methods)")
        func_name = node.func.id
        # Reverse keyword alias: _barb_if_ → if
        if func_name in _REVERSE_ALIASES:
            func_name = _REVERSE_ALIASES[func_name]
        if func_name not in functions:
            raise ExpressionError(
                f"Unknown function '{func_name}'. Available: {', '.join(sorted(functions))}"
            )
        args = [_eval_node(arg, df, functions) for arg in node.args]
        # Pass df as context for functions that need it (time functions, count)
        func = functions[func_name]
        try:
            return func(df, *args)
        except TypeError as e:
            # Only catch argument count mismatches, not internal type errors
            if "argument" in str(e) or "positional" in str(e):
                raise ExpressionError(
                    f"Wrong arguments for '{func_name}': got {len(args)} args"
                ) from e
            raise

    # List literal: [0, 1, 4] — only used with `in`
    if isinstance(node, ast.List):
        return [_eval_node(el, df, functions) for el in node.elts]

    raise ExpressionError(
        f"Unsupported expression type: {type(node).__name__}"
    )
