"""Lag functions: prev, next."""

LAG_FUNCTIONS = {
    "prev": lambda df, col, n=1: col.shift(int(n)),
    "next": lambda df, col, n=1: col.shift(-int(n)),
}

LAG_SIGNATURES = {
    "prev": "prev(col, n=1)",
    "next": "next(col, n=1)",
}

LAG_DESCRIPTIONS = {
    "prev": "value n bars ago",
    "next": "value n bars ahead",
}
