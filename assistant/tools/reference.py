"""Auto-generated function reference for the run_query tool description.

Single source of truth: reads SIGNATURES and DESCRIPTIONS from barb.functions.
Replaces the static expressions.md file.
"""

from barb.functions import DESCRIPTIONS, SIGNATURES

# Display groups: (label, function names, expanded?)
# compact = signatures on one line; expanded = one line per function with description
DISPLAY_GROUPS = [
    ("Scalar", ["abs", "log", "sqrt", "sign", "round", "if"], False),
    ("Lag", ["prev", "next"], False),
    (
        "Moving Averages",
        ["sma", "ema", "wma", "hma", "vwma", "rma"],
        False,
    ),
    (
        "Window",
        [
            "rolling_mean",
            "rolling_sum",
            "rolling_max",
            "rolling_min",
            "rolling_std",
            "rolling_count",
        ],
        False,
    ),
    ("Cumulative", ["cummax", "cummin", "cumsum"], False),
    (
        "Aggregate",
        [
            "mean",
            "sum",
            "max",
            "min",
            "std",
            "median",
            "count",
            "pct",
            "percentile",
            "correlation",
            "last",
        ],
        False,
    ),
    (
        "Time",
        [
            "dayofweek",
            "dayname",
            "hour",
            "minute",
            "month",
            "monthname",
            "year",
            "date",
            "day",
            "quarter",
        ],
        False,
    ),
    (
        "Pattern",
        [
            "streak",
            "bars_since",
            "rank",
            "rising",
            "falling",
            "valuewhen",
            "pivothigh",
            "pivotlow",
        ],
        True,
    ),
    (
        "Price",
        [
            "gap",
            "gap_pct",
            "change",
            "change_pct",
            "range",
            "range_pct",
            "midpoint",
            "typical_price",
        ],
        True,
    ),
    (
        "Candle",
        [
            "body",
            "body_pct",
            "upper_wick",
            "lower_wick",
            "green",
            "red",
            "doji",
            "inside_bar",
            "outside_bar",
        ],
        True,
    ),
    ("Signal", ["crossover", "crossunder"], True),
    (
        "Oscillators",
        [
            "rsi",
            "stoch_k",
            "stoch_d",
            "cci",
            "williams_r",
            "mfi",
            "roc",
            "momentum",
        ],
        True,
    ),
    (
        "Trend",
        [
            "macd",
            "macd_signal",
            "macd_hist",
            "adx",
            "plus_di",
            "minus_di",
            "supertrend",
            "supertrend_dir",
            "sar",
        ],
        True,
    ),
    (
        "Volatility",
        [
            "tr",
            "atr",
            "natr",
            "bbands_upper",
            "bbands_middle",
            "bbands_lower",
            "bbands_width",
            "bbands_pctb",
            "kc_upper",
            "kc_middle",
            "kc_lower",
            "kc_width",
            "donchian_upper",
            "donchian_lower",
        ],
        True,
    ),
    (
        "Volume",
        ["obv", "vwap_day", "ad_line", "volume_ratio", "volume_sma"],
        True,
    ),
    (
        "Session",
        ["session_high", "session_low", "session_open", "session_close"],
        True,
    ),
]


def build_function_reference() -> str:
    """Build the complete expression reference for the tool description."""
    sections = []

    # Base columns
    sections.append("# Expression Reference")
    sections.append("")
    sections.append("## Base columns")
    sections.append("")
    sections.append("open, high, low, close, volume — plus any columns created in `map`.")

    # Operators
    sections.append("")
    sections.append("## Operators")
    sections.append("")
    sections.append("Arithmetic: `+`, `-`, `*`, `/`, `//`, `%`, `**`")
    sections.append("Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`")
    sections.append("Boolean: `and`, `or`, `not`")
    sections.append("Membership: `dayofweek() in [0, 1, 4]`")

    # Functions
    sections.append("")
    sections.append("## Functions")

    for label, names, expanded in DISPLAY_GROUPS:
        sections.append("")
        if expanded:
            sections.append(f"{label}:")
            for name in names:
                sig = SIGNATURES[name]
                desc = DESCRIPTIONS[name]
                sections.append(f"  {sig} — {desc}")
        else:
            sigs = ", ".join(SIGNATURES[name] for name in names)
            sections.append(f"{label}: {sigs}")

    # Notes
    sections.append("")
    sections.append("## Notes")
    sections.append("")
    sections.append(
        "- Functions like atr(), gap(), stoch_k() use OHLCV from the "
        "DataFrame directly — no need to pass columns."
    )
    sections.append(
        "- Functions like rsi(col, n), ema(col, n) take an explicit "
        "column — can be applied to any series."
    )
    sections.append(
        "- prev(close) returns NaN for the first row. "
        "NaN rows are excluded from filters automatically."
    )
    sections.append("- dayofweek() returns 0=Monday, 1=Tuesday, ..., 4=Friday.")
    sections.append("- crossover(a, b) is true on the bar where a crosses above b.")

    return "\n".join(sections)
