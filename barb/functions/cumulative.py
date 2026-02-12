"""Cumulative functions: cummax, cummin, cumsum."""

CUMULATIVE_FUNCTIONS = {
    "cummax": lambda df, col: col.cummax(),
    "cummin": lambda df, col: col.cummin(),
    "cumsum": lambda df, col: col.cumsum(),
}

CUMULATIVE_SIGNATURES = {
    "cummax": "cummax(col)",
    "cummin": "cummin(col)",
    "cumsum": "cumsum(col)",
}

CUMULATIVE_DESCRIPTIONS = {
    "cummax": "running maximum",
    "cummin": "running minimum",
    "cumsum": "running total",
}
