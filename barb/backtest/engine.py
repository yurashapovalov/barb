"""Core backtest engine — simulates trades on historical data."""

import numpy as np
import pandas as pd

from barb.backtest.metrics import (
    BacktestResult,
    Trade,
    build_equity_curve,
    calculate_metrics,
)
from barb.backtest.strategy import Strategy, resolve_level
from barb.expressions import evaluate
from barb.functions import FUNCTIONS
from barb.ops import BarbError, resample

# Allowed timeframes for backtesting.
# 1m excluded: resample is no-op, millions of bars, minute exit resolution pointless.
# weekly+ excluded: too few bars, exit_bars semantics absurd.
_BACKTEST_TIMEFRAMES = {"5m", "15m", "30m", "1h", "2h", "4h", "daily"}


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    timeframe: str = "daily",
) -> BacktestResult:
    """Run a backtest on historical data.

    Args:
        df: Pre-filtered DataFrame (session/period filtering done by caller).
            Can be minute-level (will be resampled) or already at target timeframe.
        strategy: Strategy definition
        timeframe: Bar timeframe for simulation ("daily", "1h", "15m", etc.)

    Returns:
        BacktestResult with trades, metrics, and equity curve
    """
    if strategy.direction not in ("long", "short"):
        raise BarbError(
            f"Invalid direction '{strategy.direction}'. Must be 'long' or 'short'",
            error_type="ValidationError",
            step="backtest",
        )

    if timeframe not in _BACKTEST_TIMEFRAMES:
        raise BarbError(
            f"Unsupported timeframe '{timeframe}'. "
            f"Allowed: {', '.join(sorted(_BACKTEST_TIMEFRAMES))}",
            error_type="ValidationError",
            step="backtest",
        )

    if df.empty:
        return BacktestResult(trades=[], metrics=calculate_metrics([]), equity_curve=[])

    # Resample to target timeframe (no-op if already at that resolution)
    bars = resample(df, timeframe)

    if len(bars) < 2:
        return BacktestResult(trades=[], metrics=calculate_metrics([]), equity_curve=[])

    # Map each bar to its minute-level data for precise exit resolution.
    # For daily data passed directly, each bar maps to itself (1 row).
    minute_by_bar = _build_minute_index(df, bars)

    # Evaluate entry condition on all bars
    entry_mask = evaluate(strategy.entry, bars, FUNCTIONS)
    if isinstance(entry_mask, pd.Series):
        entry_mask = entry_mask.fillna(False).astype(bool)
    else:
        entry_mask = pd.Series(bool(entry_mask), index=bars.index)

    # Simulate trades
    trades = _simulate(bars, entry_mask, strategy, minute_by_bar)

    # Calculate metrics
    metrics = calculate_metrics(trades)
    equity = build_equity_curve(trades)

    return BacktestResult(trades=trades, metrics=metrics, equity_curve=equity)


def _build_minute_index(minutes: pd.DataFrame, bars: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """Map bar index → minute-level data for exit resolution.

    Uses searchsorted on sorted DatetimeIndex — O(m log n) where
    m = len(minutes), n = len(bars).
    """
    if minutes.empty or bars.empty:
        return {}

    # For each minute row, find which bar it belongs to
    indices = bars.index.searchsorted(minutes.index, side="right") - 1

    # Group by bar index
    result = {}
    unique_indices = np.unique(indices)
    for idx in unique_indices:
        if 0 <= idx < len(bars):
            mask = indices == idx
            result[int(idx)] = minutes[mask]

    return result


def _simulate(
    bars: pd.DataFrame,
    entry_mask: pd.Series,
    strategy: Strategy,
    minute_by_bar: dict[int, pd.DataFrame] | None = None,
) -> list[Trade]:
    """Bar-by-bar simulation loop.

    Uses minute bars for precise exit resolution when available.
    Falls back to daily bar checks (conservative assumption) otherwise.
    """
    trades = []
    in_position = False
    entry_price = 0.0
    entry_date = None
    entry_bar_idx = 0
    stop_price = None
    target_price = None
    tp_price = None
    trail_points = None
    best_price = None
    stop_reason = "stop"
    breakeven_activated = False
    is_long = strategy.direction == "long"
    if minute_by_bar is None:
        minute_by_bar = {}

    for i in range(len(bars)):
        bar = bars.iloc[i]
        bar_date = bars.index[i]

        if in_position:
            bars_held = i - entry_bar_idx

            # Breakeven: after N bars, if in profit, move stop to entry
            if (
                strategy.breakeven_bars is not None
                and not breakeven_activated
                and bars_held >= strategy.breakeven_bars
            ):
                in_profit = bar["open"] > entry_price if is_long else bar["open"] < entry_price
                if in_profit:
                    stop_price = entry_price
                    stop_reason = "breakeven"
                    breakeven_activated = True

            # Use minute bars for precise exit, fall back to bar-level check
            bar_minutes = minute_by_bar.get(i)
            exit_price, exit_reason, best_price = _resolve_exit(
                bar,
                bar_minutes,
                is_long,
                stop_price,
                tp_price,
                target_price,
                strategy.exit_bars,
                bars_held,
                trail_points,
                best_price,
                stop_reason,
            )

            # End of data — force close
            if exit_price is None and i == len(bars) - 1:
                exit_price = bar["close"]
                exit_reason = "end"

            if exit_price is not None:
                trades.append(
                    _build_trade(
                        entry_date,
                        bar_date,
                        entry_price,
                        exit_price,
                        strategy,
                        is_long,
                        bars_held,
                        exit_reason,
                    )
                )
                in_position = False

        elif i > 0 and entry_mask.iloc[i - 1]:
            # Signal on previous bar → enter on this bar's open
            entry_price = bar["open"]
            entry_date = bar_date
            entry_bar_idx = i

            # Apply slippage to entry
            if is_long:
                entry_price += strategy.slippage
            else:
                entry_price -= strategy.slippage

            # Calculate stop/target prices
            stop_price = _calc_stop(entry_price, strategy, is_long)
            tp_price = _calc_take_profit(entry_price, strategy, is_long)
            target_price = _calc_exit_target(bars, i - 1, strategy)

            # Initialize trailing stop
            trail_points = None
            best_price = None
            if strategy.trailing_stop is not None:
                trail_points = resolve_level(strategy.trailing_stop, entry_price)
                best_price = entry_price

            # Reset breakeven state
            stop_reason = "stop"
            breakeven_activated = False

            in_position = True

            # Check if exit happens on the same bar we entered
            bar_minutes = minute_by_bar.get(i)
            exit_price, exit_reason, best_price = _resolve_exit(
                bar,
                bar_minutes,
                is_long,
                stop_price,
                tp_price,
                target_price,
                strategy.exit_bars,
                0,
                trail_points,
                best_price,
                stop_reason,
            )

            if exit_price is not None:
                trades.append(
                    _build_trade(
                        entry_date,
                        bar_date,
                        entry_price,
                        exit_price,
                        strategy,
                        is_long,
                        0,
                        exit_reason,
                    )
                )
                in_position = False

    return trades


def _build_trade(
    entry_date,
    exit_date_raw,
    entry_price: float,
    exit_price: float,
    strategy: Strategy,
    is_long: bool,
    bars_held: int,
    exit_reason: str,
) -> Trade:
    """Create Trade with slippage and P&L calculation."""
    # Apply slippage to exit
    if is_long:
        exit_price -= strategy.slippage
        pnl = exit_price - entry_price
    else:
        exit_price += strategy.slippage
        pnl = entry_price - exit_price

    pnl -= strategy.commission

    return Trade(
        entry_date=entry_date.date() if hasattr(entry_date, "date") else entry_date,
        entry_price=round(entry_price, 4),
        exit_date=exit_date_raw.date() if hasattr(exit_date_raw, "date") else exit_date_raw,
        exit_price=round(exit_price, 4),
        direction=strategy.direction,
        pnl=round(pnl, 4),
        exit_reason=exit_reason,
        bars_held=bars_held,
    )


def _resolve_exit(
    daily_bar: pd.Series,
    day_minutes: pd.DataFrame | None,
    is_long: bool,
    stop_price: float | None,
    tp_price: float | None,
    target_price: float | None,
    exit_bars: int | None,
    bars_held: int,
    trail_points: float | None = None,
    best_price: float | None = None,
    stop_reason: str = "stop",
) -> tuple[float | None, str | None, float | None]:
    """Find exit using minute bars if available, otherwise daily bar.

    Returns (exit_price, exit_reason, best_price). best_price tracks the
    furthest favorable price for trailing stop calculation.
    """
    # Price-based exits: use minute bars when available
    if day_minutes is not None and len(day_minutes) > 0:
        exit_price, exit_reason, best_price = _find_exit_in_minutes(
            day_minutes,
            is_long,
            stop_price,
            tp_price,
            target_price,
            trail_points,
            best_price,
            stop_reason,
        )
    else:
        exit_price, exit_reason, best_price = _check_exit_levels(
            daily_bar,
            is_long,
            stop_price,
            tp_price,
            target_price,
            trail_points,
            best_price,
            stop_reason,
        )

    if exit_price is not None:
        return exit_price, exit_reason, best_price

    # Timeout — bar-level concept (exit_bars counts bars at chosen timeframe)
    if exit_bars is not None and bars_held >= exit_bars:
        return daily_bar["close"], "timeout", best_price

    return None, None, best_price


def _find_exit_in_minutes(
    minutes: pd.DataFrame,
    is_long: bool,
    stop_price: float | None,
    tp_price: float | None,
    target_price: float | None,
    trail_points: float | None = None,
    best_price: float | None = None,
    stop_reason: str = "stop",
) -> tuple[float | None, str | None, float | None]:
    """Walk minute bars chronologically to find first exit trigger.

    When trailing stop is active, best_price is updated each bar and the
    trailing stop level follows. The effective stop is the tighter of
    fixed stop_price and trailing stop (fixed acts as floor).
    """
    for _, bar in minutes.iterrows():
        # Update trailing stop from this bar's favorable price
        if trail_points is not None and best_price is not None:
            if is_long:
                best_price = max(best_price, bar["high"])
                trail_stop = best_price - trail_points
            else:
                best_price = min(best_price, bar["low"])
                trail_stop = best_price + trail_points
            effective_stop, is_trailing = _pick_tighter_stop(stop_price, trail_stop, is_long)
        else:
            effective_stop = stop_price
            is_trailing = False

        # Stop loss (fixed/breakeven or trailing)
        if effective_stop is not None:
            if is_long and bar["low"] <= effective_stop:
                reason = "trailing_stop" if is_trailing else stop_reason
                return effective_stop, reason, best_price
            if not is_long and bar["high"] >= effective_stop:
                reason = "trailing_stop" if is_trailing else stop_reason
                return effective_stop, reason, best_price

        # Take profit
        if tp_price is not None:
            if is_long and bar["high"] >= tp_price:
                return tp_price, "take_profit", best_price
            if not is_long and bar["low"] <= tp_price:
                return tp_price, "take_profit", best_price

        # Exit target
        if target_price is not None:
            if is_long and bar["high"] >= target_price:
                return target_price, "target", best_price
            if not is_long and bar["low"] <= target_price:
                return target_price, "target", best_price

    return None, None, best_price


def _check_exit_levels(
    bar: pd.Series,
    is_long: bool,
    stop_price: float | None,
    tp_price: float | None,
    target_price: float | None,
    trail_points: float | None = None,
    best_price: float | None = None,
    stop_reason: str = "stop",
) -> tuple[float | None, str | None, float | None]:
    """Check price-based exit levels on a single bar (daily fallback).

    Used when minute data is not available. Conservative assumption:
    stop checked before take-profit (pessimistic).
    """
    # Update trailing stop from this bar
    if trail_points is not None and best_price is not None:
        if is_long:
            best_price = max(best_price, bar["high"])
            trail_stop = best_price - trail_points
        else:
            best_price = min(best_price, bar["low"])
            trail_stop = best_price + trail_points
        effective_stop, is_trailing = _pick_tighter_stop(stop_price, trail_stop, is_long)
    else:
        effective_stop = stop_price
        is_trailing = False

    # 1. Stop loss (fixed/breakeven or trailing)
    if effective_stop is not None:
        if is_long and bar["low"] <= effective_stop:
            reason = "trailing_stop" if is_trailing else stop_reason
            return effective_stop, reason, best_price
        if not is_long and bar["high"] >= effective_stop:
            reason = "trailing_stop" if is_trailing else stop_reason
            return effective_stop, reason, best_price

    # 2. Take profit
    if tp_price is not None:
        if is_long and bar["high"] >= tp_price:
            return tp_price, "take_profit", best_price
        if not is_long and bar["low"] <= tp_price:
            return tp_price, "take_profit", best_price

    # 3. Exit target (fixed price from expression)
    if target_price is not None:
        if is_long and bar["high"] >= target_price:
            return target_price, "target", best_price
        if not is_long and bar["low"] <= target_price:
            return target_price, "target", best_price

    return None, None, best_price


def _pick_tighter_stop(
    fixed_stop: float | None,
    trail_stop: float,
    is_long: bool,
) -> tuple[float, bool]:
    """Return (effective_stop, is_trailing).

    Picks whichever stop is tighter (closer to current price).
    For long: higher stop = tighter. For short: lower stop = tighter.
    """
    if fixed_stop is None:
        return trail_stop, True
    if is_long:
        if trail_stop >= fixed_stop:
            return trail_stop, True
        return fixed_stop, False
    else:
        if trail_stop <= fixed_stop:
            return trail_stop, True
        return fixed_stop, False


def _calc_stop(entry_price: float, strategy: Strategy, is_long: bool) -> float | None:
    """Calculate absolute stop price."""
    if strategy.stop_loss is None:
        return None
    points = resolve_level(strategy.stop_loss, entry_price)
    return entry_price - points if is_long else entry_price + points


def _calc_take_profit(entry_price: float, strategy: Strategy, is_long: bool) -> float | None:
    """Calculate absolute take profit price."""
    if strategy.take_profit is None:
        return None
    points = resolve_level(strategy.take_profit, entry_price)
    return entry_price + points if is_long else entry_price - points


def _calc_exit_target(daily: pd.DataFrame, signal_bar_idx: int, strategy: Strategy) -> float | None:
    """Evaluate exit_target expression on the signal bar → fixed price."""
    if strategy.exit_target is None:
        return None
    # Evaluate on signal bar with enough history for indicators
    end = signal_bar_idx + 1
    start = max(0, end - 200)  # 200 bars of history for indicators
    context = daily.iloc[start:end]
    result = evaluate(strategy.exit_target, context, FUNCTIONS)
    if isinstance(result, pd.Series):
        return float(result.iloc[-1])
    return float(result)
