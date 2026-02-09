"""Scalar functions: abs, log, sqrt, sign, round, if."""

import numpy as np
import pandas as pd


def _if(df, cond, then, else_):
    """Element-wise conditional: if(cond, then, else)."""
    if isinstance(cond, pd.Series):
        return pd.Series(np.where(cond, then, else_), index=cond.index)
    return then if cond else else_


CORE_FUNCTIONS = {
    "abs": lambda df, x: x.abs() if isinstance(x, pd.Series) else abs(x),
    "log": lambda df, x: np.log(x),
    "sqrt": lambda df, x: np.sqrt(x),
    "sign": lambda df, x: np.sign(x),
    "round": lambda df, x, n=0: (
        x.round(int(n)) if isinstance(x, pd.Series) else round(x, int(n))
    ),
    "if": _if,
}

CORE_SIGNATURES = {
    "abs": "abs(x)",
    "log": "log(x)",
    "sqrt": "sqrt(x)",
    "sign": "sign(x)",
    "round": "round(x, n=0)",
    "if": "if(cond, then, else)",
}
