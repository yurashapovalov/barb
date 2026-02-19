"""Core backtest engine — simulates trades on historical data."""

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
from barb.interpreter import QueryError, filter_period, filter_session, resample


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    sessions: dict,
    session: str | None = None,
    period: str | None = None,
) -> BacktestResult:
    """Run a backtest on historical data.

    Args:
        df: Minute-level DataFrame (will be resampled to daily)
        strategy: Strategy definition
        sessions: Session config dict {"RTH": ("09:30", "16:15"), ...}
        session: Optional session filter (e.g. "RTH")
        period: Optional period filter (e.g. "2024", "2024-01:2024-06")

    Returns:
        BacktestResult with trades, metrics, and equity curve
    """
    if strategy.direction not in ("long", "short"):
        raise QueryError(
            f"Invalid direction '{strategy.direction}'. Must be 'long' or 'short'",
            error_type="ValidationError",
            step="backtest",
        )

    # Step 1: Session filter
    if session:
        df, _ = filter_session(df, session, sessions)

    # Step 2: Period filter
    if period:
        df = filter_period(df, period)

    if df.empty:
        return BacktestResult(trades=[], metrics=calculate_metrics([]), equity_curve=[])

    # Step 3: Group minute bars by date for exit resolution
    # Must happen before resample — after resample minute data is lost.
    minute_by_date = {}
    if hasattr(df.index, "time") and len(df) > 0:
        minute_by_date = {d: g for d, g in df.groupby(df.index.date)}

    # Step 4: Resample to daily
    daily = resample(df, "daily")

    if len(daily) < 2:
        return BacktestResult(trades=[], metrics=calculate_metrics([]), equity_curve=[])

    # Step 5: Evaluate entry condition on all bars
    entry_mask = evaluate(strategy.entry, daily, FUNCTIONS)
    if isinstance(entry_mask, pd.Series):
        entry_mask = entry_mask.fillna(False).astype(bool)
    else:
        # Scalar — applies to all or none
        entry_mask = pd.Series(bool(entry_mask), index=daily.index)

    # Step 6: Simulate trades
    trades = _simulate(daily, entry_mask, strategy, minute_by_date)

    # Step 7: Calculate metrics
    metrics = calculate_metrics(trades)
    equity = build_equity_curve(trades)

    return BacktestResult(trades=trades, metrics=metrics, equity_curve=equity)


def _simulate(
    daily: pd.DataFrame,
    entry_mask: pd.Series,
    strategy: Strategy,
    minute_by_date: dict | None = None,
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
    if minute_by_date is None:
        minute_by_date = {}

    for i in range(len(daily)):
        bar = daily.iloc[i]
        bar_date = daily.index[i]

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

            # Use minute bars for precise exit, fall back to daily
            day_key = bar_date.date() if hasattr(bar_date, "date") else bar_date
            day_minutes = minute_by_date.get(day_key)
            exit_price, exit_reason, best_price = _resolve_exit(
                bar,
                day_minutes,
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
            if exit_price is None and i == len(daily) - 1:
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
            target_price = _calc_exit_target(daily, i - 1, strategy)

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
            day_key = bar_date.date() if hasattr(bar_date, "date") else bar_date
            day_minutes = minute_by_date.get(day_key)
            exit_price, exit_reason, best_price = _resolve_exit(
                bar,
                day_minutes,
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

    # Timeout — daily-level concept (exit_bars counts days, not minutes)
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
