"""Barb Script function registry.

All functions receive (df, *args) where df is the current DataFrame.
New functions are added to category modules — they appear in Barb Script automatically.
"""

from barb.functions.aggregate import AGGREGATE_FUNCS, AGGREGATE_FUNCTIONS
from barb.functions.convenience import CONVENIENCE_FUNCTIONS
from barb.functions.core import CORE_FUNCTIONS
from barb.functions.oscillators import OSCILLATOR_FUNCTIONS
from barb.functions.cumulative import CUMULATIVE_FUNCTIONS
from barb.functions.lag import LAG_FUNCTIONS
from barb.functions.pattern import PATTERN_FUNCTIONS
from barb.functions.time import TIME_FUNCTIONS
from barb.functions.window import WINDOW_FUNCTIONS

FUNCTIONS = {
    **CORE_FUNCTIONS,
    **LAG_FUNCTIONS,
    **WINDOW_FUNCTIONS,
    **CUMULATIVE_FUNCTIONS,
    **PATTERN_FUNCTIONS,
    **AGGREGATE_FUNCTIONS,
    **TIME_FUNCTIONS,
    **CONVENIENCE_FUNCTIONS,
    **OSCILLATOR_FUNCTIONS,
}

__all__ = ["FUNCTIONS", "AGGREGATE_FUNCS"]
