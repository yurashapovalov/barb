"""Strategy definition for backtesting."""

from dataclasses import dataclass


@dataclass
class Strategy:
    """Trading strategy parameters.

    entry: expression that triggers a trade (e.g. "rsi(close, 14) < 30")
    direction: "long" or "short"
    exit_target: expression evaluated ONCE at entry → fixed target price
    stop_loss: fixed distance from entry — points (float) or percentage (str like "2%")
    take_profit: points (float) or percentage (str like "3%")
    trailing_stop: trail distance — stop follows price, exits on retrace. Points or "1.5%"
    exit_bars: force exit after N bars
    slippage: points per side, default 0
    commission: points per round-trip, default 0
    """

    entry: str
    direction: str  # "long" | "short"
    exit_target: str | None = None
    stop_loss: float | str | None = None
    take_profit: float | str | None = None
    trailing_stop: float | str | None = None
    exit_bars: int | None = None
    slippage: float = 0.0
    commission: float = 0.0  # points per round-trip


def resolve_level(value: float | str, entry_price: float) -> float:
    """Convert stop/target to absolute points from entry.

    Number → points as-is.
    String with % → percentage of entry price converted to points.
    """
    if isinstance(value, str) and value.endswith("%"):
        pct = float(value.rstrip("%"))
        return entry_price * pct / 100
    return float(value)
