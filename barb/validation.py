"""Pre-validate all expressions in a Barb Script query.

Catches syntax errors, unknown functions, and unsupported operators
across ALL fields at once — before the pipeline executes.
No DataFrame required.
"""

import ast
import re

from barb.expressions import (
    _BINARY_OPS,
    _COMPARE_OPS,
    _REVERSE_ALIASES,
    _preprocess_keywords,
)
from barb.functions import AGGREGATE_FUNCS, FUNCTIONS


class ValidationError(Exception):
    """Raised when pre-validation finds one or more expression errors."""

    def __init__(self, errors: list[dict]):
        self.errors = errors
        messages = [e["message"] for e in errors]
        super().__init__(f"{len(errors)} expression error(s): {'; '.join(messages)}")


# Standalone = not part of ==, !=, <=, >=
_LONE_EQUALS_RE = re.compile(r"(?<![=!<>])=(?!=)")

# Group aggregate pattern: func(col) or count()
_AGG_EXPR_RE = re.compile(r"^(\w+)\((\w+)?\)$")

_KNOWN_FUNCTIONS = set(FUNCTIONS.keys())


def validate_expressions(query: dict) -> None:
    """Pre-validate all expression fields in a query.

    Checks syntax, function names, operator whitelist, and group_by format.
    Collects ALL errors and raises ValidationError if any found.
    Does NOT require a DataFrame.
    """
    errors: list[dict] = []

    # map expressions
    if isinstance(query.get("map"), dict):
        for name, expr in query["map"].items():
            if not isinstance(expr, str):
                errors.append({
                    "step": "map",
                    "expression": str(expr),
                    "message": (
                        f"map['{name}'] must be a string expression, "
                        f"got {type(expr).__name__}"
                    ),
                })
                continue
            _check_expression(expr, f"map['{name}']", "map", errors)

    # where expression
    where = query.get("where")
    if isinstance(where, str):
        _check_expression(where, "where", "where", errors)

    # select expression(s)
    select = query.get("select")
    if isinstance(select, str):
        group_by = query.get("group_by")
        _check_select(select, group_by, errors)

    # group_by: detect function calls (common LLM mistake)
    group_by = query.get("group_by")
    if isinstance(group_by, str) and "(" in group_by:
        col_name = _suggest_column_name(group_by)
        errors.append({
            "step": "group_by",
            "expression": group_by,
            "message": (
                "group_by must be a column name, not an expression. "
                "Create the column in 'map' first, then group by it."
            ),
            "hint": f'Use map: {{"{col_name}": "{group_by}"}}, then group_by: "{col_name}"',
        })
    elif isinstance(group_by, list):
        for col in group_by:
            if isinstance(col, str) and "(" in col:
                errors.append({
                    "step": "group_by",
                    "expression": col,
                    "message": (
                        f"group_by must be column names, not expressions. "
                        f"Create '{col}' in 'map' first."
                    ),
                })

    if errors:
        raise ValidationError(errors)


def _check_expression(expr: str, label: str, step: str, errors: list[dict]) -> None:
    """Check a single expression for syntax errors, unknown functions, bad operators."""
    # Detect lone = that should be ==
    if _LONE_EQUALS_RE.search(expr):
        errors.append({
            "step": step,
            "expression": expr,
            "message": f"Syntax error in {label}: use '==' for comparison, not '='",
            "hint": "Replace '=' with '=='.",
        })
        return  # ast.parse will also fail; skip to avoid duplicate

    preprocessed = _preprocess_keywords(expr)
    try:
        tree = ast.parse(preprocessed, mode="eval")
    except SyntaxError as e:
        errors.append({
            "step": step,
            "expression": expr,
            "message": f"Syntax error in {label}: {e.msg}",
        })
        return

    _walk_ast(tree.body, label, step, errors)


def _walk_ast(node: ast.AST, label: str, step: str, errors: list[dict]) -> None:
    """Recursively walk AST and check function names and operators."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in _REVERSE_ALIASES:
                func_name = _REVERSE_ALIASES[func_name]
            if func_name not in _KNOWN_FUNCTIONS:
                errors.append({
                    "step": step,
                    "expression": ast.unparse(node),
                    "message": (
                        f"Unknown function '{func_name}' in {label}. "
                        f"Available: {', '.join(sorted(_KNOWN_FUNCTIONS))}"
                    ),
                })
        else:
            errors.append({
                "step": step,
                "expression": ast.unparse(node),
                "message": f"Only simple function calls allowed in {label} (no methods).",
            })
        for arg in node.args:
            _walk_ast(arg, label, step, errors)
        return

    if isinstance(node, ast.BinOp):
        if type(node.op) not in _BINARY_OPS:
            errors.append({
                "step": step,
                "expression": ast.unparse(node),
                "message": f"Unsupported operator '{type(node.op).__name__}' in {label}",
            })
        _walk_ast(node.left, label, step, errors)
        _walk_ast(node.right, label, step, errors)
        return

    if isinstance(node, ast.Compare):
        _walk_ast(node.left, label, step, errors)
        for op, comp in zip(node.ops, node.comparators):
            if type(op) not in _COMPARE_OPS and not isinstance(op, (ast.In, ast.NotIn)):
                errors.append({
                    "step": step,
                    "expression": ast.unparse(node),
                    "message": f"Unsupported comparison '{type(op).__name__}' in {label}",
                })
            _walk_ast(comp, label, step, errors)
        return

    if isinstance(node, ast.BoolOp):
        for value in node.values:
            _walk_ast(value, label, step, errors)
        return

    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, (ast.USub, ast.Not)):
            errors.append({
                "step": step,
                "expression": ast.unparse(node),
                "message": f"Unsupported unary operator '{type(node.op).__name__}' in {label}",
            })
        _walk_ast(node.operand, label, step, errors)
        return

    if isinstance(node, ast.List):
        for el in node.elts:
            _walk_ast(el, label, step, errors)
        return

    if isinstance(node, (ast.Name, ast.Constant)):
        return

    errors.append({
        "step": step,
        "expression": ast.unparse(node),
        "message": f"Unsupported expression type '{type(node).__name__}' in {label}",
    })


def _check_select(select_raw: str, group_by, errors: list[dict]) -> None:
    """Check select expressions. Handles comma-separated lists."""
    if "," in select_raw:
        parts = [s.strip() for s in select_raw.split(",") if s.strip()]
    else:
        parts = [select_raw.strip()]

    for s in parts:
        if group_by:
            _check_group_select(s, errors)
        else:
            _check_expression(s, "select", "select", errors)


def _check_group_select(expr: str, errors: list[dict]) -> None:
    """Check a select expression in group_by context (must be func(col) or count())."""
    expr = expr.strip()
    if expr == "count()":
        return

    match = _AGG_EXPR_RE.match(expr)
    if not match:
        errors.append({
            "step": "select",
            "expression": expr,
            "message": (
                f"Cannot parse aggregate expression: '{expr}'. "
                "Expected: func(column) or count()"
            ),
        })
        return

    func_name = match.group(1)
    if func_name not in AGGREGATE_FUNCS:
        errors.append({
            "step": "select",
            "expression": expr,
            "message": (
                f"Unknown aggregate function '{func_name}'. "
                f"Available: {', '.join(sorted(AGGREGATE_FUNCS))}"
            ),
        })


def _suggest_column_name(expr: str) -> str:
    """Suggest a column name for a function expression: dayofweek() → weekday."""
    match = re.match(r"(\w+)\(", expr)
    if not match:
        return "col"
    func = match.group(1)
    suggestions = {"dayofweek": "weekday", "dayname": "day_name", "monthname": "month_name"}
    return suggestions.get(func, func)
