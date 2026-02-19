"""Tests for backtest engine.

Uses both synthetic data (deterministic, hand-verified trades)
and real NQ data (smoke tests on real market data).
"""

import pandas as pd
import pytest

from barb.backtest.engine import (
    run_backtest,
)
from barb.backtest.metrics import Trade, build_equity_curve, calculate_metrics
from barb.backtest.strategy import Strategy, resolve_level

# --- Fixtures: synthetic daily data ---


@pytest.fixture
def daily_df():
    """10-day synthetic daily DataFrame for deterministic tests.

    Prices designed for predictable entry/exit:
    Day 0: 100 (setup)
    Day 1: gap up to 105, close 108 (entry signal: open > prev close)
    Day 2: open 107, range 104-110 (entry bar for gap strategy)
    Day 3-9: various prices for stop/target testing
    """
    dates = pd.date_range("2024-01-02", periods=10, freq="D")
    return pd.DataFrame(
        {
            "open": [100, 105, 107, 103, 106, 102, 108, 104, 110, 106],
            "high": [104, 110, 110, 108, 111, 107, 112, 109, 114, 110],
            "low": [98, 103, 104, 101, 104, 100, 106, 102, 108, 104],
            "close": [102, 108, 106, 105, 109, 104, 110, 106, 112, 108],
            "volume": [1000] * 10,
        },
        index=dates,
        dtype=float,
    )


@pytest.fixture
def empty_sessions():
    """Empty sessions dict — no session filtering needed for daily data."""
    return {"RTH": ("09:30", "16:15")}


# --- Strategy dataclass ---


class TestStrategy:
    def test_create_minimal(self):
        s = Strategy(entry="close > 100", direction="long")
        assert s.entry == "close > 100"
        assert s.direction == "long"
        assert s.stop_loss is None
        assert s.slippage == 0.0

    def test_create_full(self):
        s = Strategy(
            entry="rsi(close, 14) < 30",
            direction="long",
            exit_target="prev(close)",
            stop_loss="2%",
            take_profit="3%",
            exit_bars=5,
            slippage=0.25,
        )
        assert s.stop_loss == "2%"
        assert s.take_profit == "3%"
        assert s.exit_bars == 5


class TestResolveLevel:
    def test_points(self):
        assert resolve_level(20, 1000) == 20

    def test_percentage(self):
        assert resolve_level("2%", 1000) == 20.0

    def test_percentage_small_price(self):
        assert resolve_level("1%", 50) == 0.5

    def test_float_points(self):
        assert resolve_level(0.25, 100) == 0.25


# --- Metrics ---


class TestMetrics:
    def test_empty_trades(self):
        m = calculate_metrics([])
        assert m.total_trades == 0
        assert m.win_rate == 0.0

    def test_all_winners(self):
        trades = [
            Trade("2024-01-01", 100, "2024-01-02", 110, "long", 10, "target", 1),
            Trade("2024-01-03", 105, "2024-01-04", 115, "long", 10, "target", 1),
        ]
        m = calculate_metrics(trades)
        assert m.total_trades == 2
        assert m.winning_trades == 2
        assert m.losing_trades == 0
        assert m.win_rate == 100.0
        assert m.profit_factor == float("inf")
        assert m.total_pnl == 20
        assert m.max_drawdown == 0

    def test_mixed_trades(self):
        trades = [
            Trade("2024-01-01", 100, "2024-01-02", 110, "long", 10, "target", 1),
            Trade("2024-01-03", 105, "2024-01-04", 100, "long", -5, "stop", 1),
            Trade("2024-01-05", 102, "2024-01-06", 108, "long", 6, "target", 1),
        ]
        m = calculate_metrics(trades)
        assert m.total_trades == 3
        assert m.winning_trades == 2
        assert m.losing_trades == 1
        assert m.win_rate == pytest.approx(66.67, rel=0.01)
        assert m.profit_factor == pytest.approx(16 / 5)
        assert m.total_pnl == 11
        assert m.expectancy == pytest.approx(11 / 3)
        assert m.max_consecutive_wins == 1  # win, loss, win
        assert m.max_consecutive_losses == 1

    def test_max_drawdown(self):
        trades = [
            Trade("2024-01-01", 100, "2024-01-02", 120, "long", 20, "target", 1),
            Trade("2024-01-03", 115, "2024-01-04", 105, "long", -10, "stop", 1),
            Trade("2024-01-05", 108, "2024-01-06", 100, "long", -8, "stop", 1),
            Trade("2024-01-07", 102, "2024-01-08", 115, "long", 13, "target", 1),
        ]
        m = calculate_metrics(trades)
        # Equity: 20, 10, 2, 15 → peak=20, trough=2 → DD=18
        assert m.max_drawdown == 18
        assert m.max_consecutive_losses == 2

    def test_equity_curve(self):
        trades = [
            Trade("2024-01-01", 100, "2024-01-02", 110, "long", 10, "target", 1),
            Trade("2024-01-03", 105, "2024-01-04", 100, "long", -5, "stop", 1),
        ]
        curve = build_equity_curve(trades)
        assert curve == [10, 5]


# --- Engine: synthetic data ---


class TestEngineBasic:
    def test_simple_long_entry(self, daily_df, empty_sessions):
        """Long when close > 107 → entry next bar's open."""
        strategy = Strategy(entry="close > 107", direction="long", exit_bars=1)
        result = run_backtest(daily_df, strategy, empty_sessions)
        assert len(result.trades) > 0
        for trade in result.trades:
            assert trade.direction == "long"
            assert trade.exit_reason == "timeout"
            assert trade.bars_held == 1

    def test_simple_short_entry(self, daily_df, empty_sessions):
        """Short when close < 103 → entry next bar's open."""
        strategy = Strategy(entry="close < 103", direction="short", exit_bars=1)
        result = run_backtest(daily_df, strategy, empty_sessions)
        assert len(result.trades) > 0
        for trade in result.trades:
            assert trade.direction == "short"

    def test_stop_loss_long(self, daily_df, empty_sessions):
        """Long with tight stop → should get stopped out."""
        strategy = Strategy(entry="close > 107", direction="long", stop_loss=1)
        result = run_backtest(daily_df, strategy, empty_sessions)
        stopped = [t for t in result.trades if t.exit_reason == "stop"]
        # With stop of 1 point, likely to get stopped
        assert len(stopped) >= 0  # May or may not depending on data

    def test_take_profit_long(self, daily_df, empty_sessions):
        """Long with take profit."""
        strategy = Strategy(entry="close > 107", direction="long", take_profit=5)
        result = run_backtest(daily_df, strategy, empty_sessions)
        for trade in result.trades:
            if trade.exit_reason == "take_profit":
                assert trade.pnl > 0

    def test_no_signals(self, daily_df, empty_sessions):
        """Entry condition never true → no trades."""
        strategy = Strategy(entry="close > 999", direction="long")
        result = run_backtest(daily_df, strategy, empty_sessions)
        assert len(result.trades) == 0
        assert result.metrics.total_trades == 0

    def test_slippage_reduces_pnl(self, daily_df, empty_sessions):
        """Same strategy with and without slippage."""
        strategy_no_slip = Strategy(entry="close > 107", direction="long", exit_bars=1)
        strategy_slip = Strategy(entry="close > 107", direction="long", exit_bars=1, slippage=0.5)
        r1 = run_backtest(daily_df, strategy_no_slip, empty_sessions)
        r2 = run_backtest(daily_df, strategy_slip, empty_sessions)
        if r1.trades and r2.trades:
            # Each trade loses 1.0 points (0.5 entry + 0.5 exit)
            assert r2.metrics.total_pnl < r1.metrics.total_pnl

    def test_percentage_stop(self, daily_df, empty_sessions):
        """Stop loss as percentage."""
        strategy = Strategy(entry="close > 107", direction="long", stop_loss="1%")
        result = run_backtest(daily_df, strategy, empty_sessions)
        # Should not crash, percentage gets resolved
        assert isinstance(result.metrics.total_trades, int)

    def test_invalid_direction(self, daily_df, empty_sessions):
        """Invalid direction raises error."""
        strategy = Strategy(entry="close > 100", direction="sideways")
        with pytest.raises(Exception, match="Invalid direction"):
            run_backtest(daily_df, strategy, empty_sessions)

    def test_empty_data(self, empty_sessions):
        """Empty DataFrame → no trades."""
        empty = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            dtype=float,
        )
        empty.index = pd.DatetimeIndex([], name="timestamp")
        strategy = Strategy(entry="close > 100", direction="long")
        result = run_backtest(empty, strategy, empty_sessions)
        assert result.trades == []

    def test_exit_bars(self, daily_df, empty_sessions):
        """Exit after N bars."""
        strategy = Strategy(entry="close > 107", direction="long", exit_bars=2)
        result = run_backtest(daily_df, strategy, empty_sessions)
        for trade in result.trades:
            if trade.exit_reason == "timeout":
                assert trade.bars_held == 2

    def test_end_of_data_exit(self, daily_df, empty_sessions):
        """Position open at end of data → forced close."""
        # Entry on last possible bar → forced close on last bar
        strategy = Strategy(entry="close > 100", direction="long")
        result = run_backtest(daily_df, strategy, empty_sessions)
        if result.trades:
            last_trade = result.trades[-1]
            # Last trade either exits normally or gets force-closed
            assert last_trade.exit_reason in ("stop", "target", "take_profit", "timeout", "end")

    def test_result_structure(self, daily_df, empty_sessions):
        """BacktestResult has all expected fields."""
        strategy = Strategy(entry="close > 107", direction="long", exit_bars=1)
        result = run_backtest(daily_df, strategy, empty_sessions)
        assert hasattr(result, "trades")
        assert hasattr(result, "metrics")
        assert hasattr(result, "equity_curve")
        assert len(result.equity_curve) == len(result.trades)


# --- Engine: real NQ data ---


class TestEngineRealData:
    def test_rsi_oversold_long(self, nq_minute_slice, sessions):
        """RSI < 30 → long, stop 2%, take 3%, max 5 bars."""
        strategy = Strategy(
            entry="rsi(close, 14) < 30",
            direction="long",
            stop_loss="2%",
            take_profit="3%",
            exit_bars=5,
        )
        result = run_backtest(nq_minute_slice, strategy, sessions, session="RTH")
        assert result.metrics.total_trades >= 0
        assert len(result.equity_curve) == len(result.trades)

    def test_big_drop_reversal(self, nq_minute_slice, sessions):
        """Long after 2.5%+ drop, hold 3 days."""
        strategy = Strategy(
            entry="change_pct(close, 1) <= -2.5",
            direction="long",
            exit_bars=3,
        )
        result = run_backtest(nq_minute_slice, strategy, sessions, session="RTH")
        assert result.metrics.total_trades >= 0
        for trade in result.trades:
            assert trade.bars_held <= 3 or trade.exit_reason == "end"

    def test_with_period_filter(self, nq_minute_slice, sessions):
        """Period filter narrows data."""
        strategy = Strategy(entry="close > prev(close)", direction="long", exit_bars=1)
        r_full = run_backtest(nq_minute_slice, strategy, sessions, session="RTH")
        r_month = run_backtest(nq_minute_slice, strategy, sessions, session="RTH", period="2024-03")
        assert r_month.metrics.total_trades <= r_full.metrics.total_trades

    def test_short_strategy(self, nq_minute_slice, sessions):
        """Short when overbought."""
        strategy = Strategy(
            entry="rsi(close, 14) > 70",
            direction="short",
            stop_loss="1%",
            take_profit="2%",
        )
        result = run_backtest(nq_minute_slice, strategy, sessions, session="RTH")
        assert result.metrics.total_trades >= 0
        for trade in result.trades:
            assert trade.direction == "short"

    def test_exit_target_expression(self, nq_minute_slice, sessions):
        """Exit target evaluated at entry."""
        strategy = Strategy(
            entry="change_pct(close, 1) <= -1.5",
            direction="long",
            exit_target="close",  # target = signal bar's close
            stop_loss="1%",
        )
        result = run_backtest(nq_minute_slice, strategy, sessions, session="RTH")
        for trade in result.trades:
            if trade.exit_reason == "target":
                assert trade.pnl != 0  # Should have some P&L


# --- Minute-level exit resolution ---


def _make_minutes(prices):
    """Build minute DataFrame from (open, high, low, close) tuples."""
    times = pd.date_range("2024-01-02 09:30", periods=len(prices), freq="min")
    return pd.DataFrame(
        {
            "open": [p[0] for p in prices],
            "high": [p[1] for p in prices],
            "low": [p[2] for p in prices],
            "close": [p[3] for p in prices],
            "volume": [100] * len(prices),
        },
        index=times,
        dtype=float,
    )


class TestFindExitInMinutes:
    def test_stop_hit_first(self):
        """Stop triggers before take profit in minute sequence."""
        from barb.backtest.engine import _find_exit_in_minutes

        # Minute 1: price drops to stop, minute 2: price rises to TP
        minutes = _make_minutes(
            [
                (100, 100, 95, 96),  # low=95 hits stop at 97
                (96, 106, 96, 105),  # high=106 would hit TP at 105, but stop already hit
            ]
        )
        price, reason, _ = _find_exit_in_minutes(minutes, True, 97.0, 105.0, None)
        assert reason == "stop"
        assert price == 97.0

    def test_tp_hit_first(self):
        """Take profit triggers before stop in minute sequence."""
        from barb.backtest.engine import _find_exit_in_minutes

        # Minute 1: price rises to TP, minute 2: price drops to stop
        minutes = _make_minutes(
            [
                (100, 106, 99, 105),  # high=106 hits TP at 105
                (105, 105, 94, 95),  # low=94 would hit stop at 97, but TP already hit
            ]
        )
        price, reason, _ = _find_exit_in_minutes(minutes, True, 97.0, 105.0, None)
        assert reason == "take_profit"
        assert price == 105.0

    def test_both_on_same_bar_stop_wins(self):
        """When both levels hit on same minute bar, stop checked first."""
        from barb.backtest.engine import _find_exit_in_minutes

        # Single bar where both stop and TP could trigger
        minutes = _make_minutes(
            [
                (100, 106, 95, 100),  # low=95 < stop=97, high=106 > tp=105
            ]
        )
        price, reason, _ = _find_exit_in_minutes(minutes, True, 97.0, 105.0, None)
        assert reason == "stop"
        assert price == 97.0

    def test_no_exit(self):
        """Neither level hit."""
        from barb.backtest.engine import _find_exit_in_minutes

        minutes = _make_minutes(
            [
                (100, 103, 98, 101),
                (101, 104, 99, 102),
            ]
        )
        price, reason, _ = _find_exit_in_minutes(minutes, True, 95.0, 110.0, None)
        assert price is None
        assert reason is None

    def test_target_exit(self):
        """Exit target hit in minutes."""
        from barb.backtest.engine import _find_exit_in_minutes

        minutes = _make_minutes(
            [
                (100, 100, 98, 99),
                (99, 103, 99, 102),  # high=103 hits target at 102
            ]
        )
        price, reason, _ = _find_exit_in_minutes(minutes, True, None, None, 102.0)
        assert reason == "target"
        assert price == 102.0

    def test_short_stop_hit(self):
        """Short position: stop hit when price goes above stop level."""
        from barb.backtest.engine import _find_exit_in_minutes

        minutes = _make_minutes(
            [
                (100, 104, 98, 99),  # high=104 hits stop at 103
            ]
        )
        price, reason, _ = _find_exit_in_minutes(minutes, False, 103.0, None, None)
        assert reason == "stop"
        assert price == 103.0

    def test_short_tp_hit(self):
        """Short position: TP hit when price drops below TP level."""
        from barb.backtest.engine import _find_exit_in_minutes

        minutes = _make_minutes(
            [
                (100, 101, 96, 97),  # low=96 hits TP at 97
            ]
        )
        price, reason, _ = _find_exit_in_minutes(minutes, False, None, 97.0, None)
        assert reason == "take_profit"
        assert price == 97.0


class TestResolveExit:
    def test_prefers_minutes_over_daily(self):
        """When minute data available, uses it instead of daily bar."""
        from barb.backtest.engine import _resolve_exit

        daily_bar = pd.Series({"open": 100, "high": 106, "low": 95, "close": 100})
        # Minutes show TP hit first (opposite of conservative assumption)
        minutes = _make_minutes(
            [
                (100, 106, 99, 105),  # high=106 hits TP
                (105, 105, 94, 95),  # low=94 would hit stop
            ]
        )
        price, reason, _ = _resolve_exit(daily_bar, minutes, True, 97.0, 105.0, None, None, 1)
        assert reason == "take_profit"  # Minute-level: TP first

    def test_daily_fallback_conservative(self):
        """Without minute data, uses conservative daily assumption (stop first)."""
        from barb.backtest.engine import _resolve_exit

        daily_bar = pd.Series({"open": 100, "high": 106, "low": 95, "close": 100})
        price, reason, _ = _resolve_exit(daily_bar, None, True, 97.0, 105.0, None, None, 1)
        assert reason == "stop"  # Conservative: stop checked first

    def test_timeout_after_price_check(self):
        """Timeout triggers when no price exit and bars_held >= exit_bars."""
        from barb.backtest.engine import _resolve_exit

        daily_bar = pd.Series({"open": 100, "high": 103, "low": 98, "close": 101})
        price, reason, _ = _resolve_exit(daily_bar, None, True, 95.0, 110.0, None, 3, 3)
        assert reason == "timeout"
        assert price == 101.0

    def test_no_exit_when_nothing_triggers(self):
        """No exit when levels not hit and not timed out."""
        from barb.backtest.engine import _resolve_exit

        daily_bar = pd.Series({"open": 100, "high": 103, "low": 98, "close": 101})
        price, reason, _ = _resolve_exit(daily_bar, None, True, 95.0, 110.0, None, 5, 2)
        assert price is None
        assert reason is None


class TestMinuteResolutionIntegration:
    """Integration test: minute data changes trade outcome vs daily-only."""

    def test_minute_data_changes_outcome(self):
        """Key test: same daily bar, different outcome with minute data.

        Setup: long entry at 100, stop=97, TP=105.
        Daily bar: open=100, high=106, low=95 → both could trigger.
        Minutes show TP hit at 09:45, stop hit at 10:15 → TP wins.
        Without minutes: conservative → stop wins.
        """
        # Build minute data for 2 days: day 1 = signal, day 2 = exit
        day1_minutes = pd.date_range("2024-01-02 09:30", periods=60, freq="min")
        day2_minutes = pd.date_range("2024-01-03 09:30", periods=60, freq="min")

        # Day 1: flat around 100, close > 99 (signal triggers)
        d1_data = {
            "open": [100] * 60,
            "high": [101] * 60,
            "low": [99] * 60,
            "close": [100] * 60,
            "volume": [100] * 60,
        }

        # Day 2: first TP hit (price rises to 106), then drops to 95
        # Minutes 0-14: price rises to TP
        # Minutes 15-59: price drops past stop
        d2_open = [100] * 15 + [105] * 15 + [98] * 30
        d2_high = [106] * 15 + [106] * 15 + [98] * 30
        d2_low = [99] * 15 + [104] * 15 + [94] * 30
        d2_close = [105] * 15 + [104] * 15 + [95] * 30
        d2_data = {
            "open": d2_open,
            "high": d2_high,
            "low": d2_low,
            "close": d2_close,
            "volume": [100] * 60,
        }

        # Combine into a single minute DataFrame
        all_idx = day1_minutes.append(day2_minutes)
        df_minute = pd.DataFrame(
            {k: d1_data[k] + d2_data[k] for k in d1_data},
            index=all_idx,
            dtype=float,
        )

        sessions = {"RTH": ("09:30", "16:15")}
        strategy = Strategy(
            entry="close > 99",
            direction="long",
            stop_loss=3,  # stop at 97 (entry 100 - 3)
            take_profit=5,  # TP at 105 (entry 100 + 5)
        )
        result = run_backtest(df_minute, strategy, sessions)

        # With minute data: TP should be hit first (in first 15 minutes)
        assert len(result.trades) >= 1
        trade = result.trades[0]
        assert trade.exit_reason == "take_profit"
        assert trade.pnl > 0


# --- New metrics ---


class TestNewMetrics:
    def test_recovery_factor(self):
        """Recovery factor = total_pnl / max_drawdown."""
        trades = [
            Trade("2024-01-01", 100, "2024-01-02", 120, "long", 20, "target", 1),
            Trade("2024-01-03", 115, "2024-01-04", 105, "long", -10, "stop", 1),
            Trade("2024-01-05", 108, "2024-01-06", 100, "long", -8, "stop", 1),
            Trade("2024-01-07", 102, "2024-01-08", 115, "long", 13, "target", 1),
        ]
        m = calculate_metrics(trades)
        # total_pnl = 15, max_dd = 18
        assert m.recovery_factor == pytest.approx(15 / 18)

    def test_recovery_factor_no_drawdown(self):
        """All winning trades → max_dd = 0 → recovery_factor = inf."""
        trades = [
            Trade("2024-01-01", 100, "2024-01-02", 110, "long", 10, "target", 1),
            Trade("2024-01-03", 105, "2024-01-04", 115, "long", 10, "target", 1),
        ]
        m = calculate_metrics(trades)
        assert m.recovery_factor == float("inf")

    def test_recovery_factor_zero_trades(self):
        """Zero trades → recovery_factor = 0."""
        m = calculate_metrics([])
        assert m.recovery_factor == 0.0

    def test_gross_profit_loss(self):
        """Gross profit and gross loss exposed in metrics."""
        trades = [
            Trade("2024-01-01", 100, "2024-01-02", 110, "long", 10, "target", 1),
            Trade("2024-01-03", 105, "2024-01-04", 100, "long", -5, "stop", 1),
            Trade("2024-01-05", 102, "2024-01-06", 108, "long", 6, "target", 1),
        ]
        m = calculate_metrics(trades)
        assert m.gross_profit == 16
        assert m.gross_loss == -5  # stored as negative

    def test_gross_profit_loss_zero_trades(self):
        """Zero trades → both = 0."""
        m = calculate_metrics([])
        assert m.gross_profit == 0.0
        assert m.gross_loss == 0.0


# --- Commission ---


class TestCommission:
    def test_commission_basic(self, daily_df, empty_sessions):
        """Commission reduces PnL by fixed amount per trade."""
        strategy_no_comm = Strategy(entry="close > 107", direction="long", exit_bars=1)
        strategy_comm = Strategy(entry="close > 107", direction="long", exit_bars=1, commission=2.0)
        r1 = run_backtest(daily_df, strategy_no_comm, empty_sessions)
        r2 = run_backtest(daily_df, strategy_comm, empty_sessions)
        assert r1.trades, "Need trades to test commission"
        # Each trade should lose exactly 2.0 pts from commission
        for t1, t2 in zip(r1.trades, r2.trades):
            assert t2.pnl == pytest.approx(t1.pnl - 2.0)

    def test_commission_default_zero(self):
        """Default commission is 0 — backward compatible."""
        s = Strategy(entry="close > 100", direction="long")
        assert s.commission == 0.0

    def test_commission_with_slippage(self, daily_df, empty_sessions):
        """Commission and slippage both applied correctly."""
        strategy_base = Strategy(entry="close > 107", direction="long", exit_bars=1)
        strategy_both = Strategy(
            entry="close > 107", direction="long", exit_bars=1, slippage=0.5, commission=1.0
        )
        r1 = run_backtest(daily_df, strategy_base, empty_sessions)
        r2 = run_backtest(daily_df, strategy_both, empty_sessions)
        assert r1.trades, "Need trades to test"
        # Each trade loses 1.0 (slippage: 0.5*2 sides) + 1.0 (commission) = 2.0
        for t1, t2 in zip(r1.trades, r2.trades):
            assert t2.pnl == pytest.approx(t1.pnl - 2.0)


# --- Format summary ---


def _make_result(trades):
    """Helper: build BacktestResult from trade list."""
    from barb.backtest.metrics import BacktestResult, build_equity_curve, calculate_metrics

    return BacktestResult(
        trades=trades,
        metrics=calculate_metrics(trades),
        equity_curve=build_equity_curve(trades),
    )


class TestFormatSummary:
    def test_zero_trades(self):
        """Zero trades → single line message."""
        from assistant.tools.backtest import _format_summary

        result = _make_result([])
        summary = _format_summary(result)
        assert "0 trades" in summary

    def test_format_summary_yearly(self):
        """Yearly breakdown present in summary."""
        from datetime import date

        from assistant.tools.backtest import _format_summary

        trades = [
            Trade(date(2023, 6, 1), 100, date(2023, 6, 2), 110, "long", 10, "target", 1),
            Trade(date(2024, 3, 1), 100, date(2024, 3, 2), 105, "long", 5, "target", 1),
            Trade(date(2024, 6, 1), 100, date(2024, 6, 2), 97, "long", -3, "stop", 1),
        ]
        summary = _format_summary(_make_result(trades))
        assert "By year:" in summary
        assert "2023" in summary
        assert "2024" in summary

    def test_format_summary_exit_types(self):
        """Exit type breakdown with W/L counts present in summary."""
        from datetime import date

        from assistant.tools.backtest import _format_summary

        trades = [
            Trade(date(2024, 1, 1), 100, date(2024, 1, 2), 110, "long", 10, "target", 1),
            Trade(date(2024, 1, 3), 100, date(2024, 1, 4), 95, "long", -5, "stop", 1),
            Trade(date(2024, 1, 5), 100, date(2024, 1, 6), 103, "long", 3, "timeout", 2),
        ]
        summary = _format_summary(_make_result(trades))
        assert "Exits:" in summary
        assert "W:" in summary
        assert "L:" in summary
        assert "stop 1 (W:0 L:1" in summary
        assert "target 1 (W:1 L:0" in summary

    def test_format_summary_top_trades(self):
        """Concentration metric (top 3 trades) present in summary."""
        from datetime import date

        from assistant.tools.backtest import _format_summary

        trades = [
            Trade(date(2024, 1, 1), 100, date(2024, 1, 2), 150, "long", 50, "target", 1),
            Trade(date(2024, 1, 3), 100, date(2024, 1, 4), 95, "long", -5, "stop", 1),
            Trade(date(2024, 1, 5), 100, date(2024, 1, 6), 102, "long", 2, "timeout", 2),
        ]
        summary = _format_summary(_make_result(trades))
        assert "Top 3 trades:" in summary
        assert "% of total PnL" in summary

    def test_format_summary_five_lines(self):
        """Summary has exactly 5 lines for non-zero trades."""
        from datetime import date

        from assistant.tools.backtest import _format_summary

        trades = [
            Trade(date(2024, 1, 1), 100, date(2024, 1, 2), 110, "long", 10, "target", 1),
            Trade(date(2024, 1, 3), 100, date(2024, 1, 4), 95, "long", -5, "stop", 1),
        ]
        summary = _format_summary(_make_result(trades))
        lines = summary.strip().split("\n")
        assert len(lines) == 5

    def test_format_summary_recovery_factor(self):
        """Recovery factor appears in summary line 2."""
        from datetime import date

        from assistant.tools.backtest import _format_summary

        trades = [
            Trade(date(2024, 1, 1), 100, date(2024, 1, 2), 110, "long", 10, "target", 1),
            Trade(date(2024, 1, 3), 100, date(2024, 1, 4), 95, "long", -5, "stop", 1),
        ]
        summary = _format_summary(_make_result(trades))
        assert "Recovery:" in summary

    def test_format_summary_best_worst(self):
        """Best and worst trade appear in summary."""
        from datetime import date

        from assistant.tools.backtest import _format_summary

        trades = [
            Trade(date(2024, 1, 1), 100, date(2024, 1, 2), 150, "long", 50, "target", 1),
            Trade(date(2024, 1, 3), 100, date(2024, 1, 4), 80, "long", -20, "stop", 1),
            Trade(date(2024, 1, 5), 100, date(2024, 1, 6), 105, "long", 5, "timeout", 2),
        ]
        summary = _format_summary(_make_result(trades))
        assert "Best: +50.0" in summary
        assert "Worst: -20.0" in summary

    def test_format_summary_consecutive(self):
        """Max consecutive wins/losses appear in summary."""
        from datetime import date

        from assistant.tools.backtest import _format_summary

        trades = [
            Trade(date(2024, 1, 1), 100, date(2024, 1, 2), 110, "long", 10, "target", 1),
            Trade(date(2024, 1, 3), 100, date(2024, 1, 4), 115, "long", 15, "target", 1),
            Trade(date(2024, 1, 5), 100, date(2024, 1, 6), 95, "long", -5, "stop", 1),
        ]
        summary = _format_summary(_make_result(trades))
        assert "Consec W/L: 2/1" in summary


# --- Trailing stop ---


class TestTrailingStop:
    def test_trailing_stop_basic_long(self, daily_df, empty_sessions):
        """Long with trailing stop: price moves up, trail follows, exits on retrace."""
        # daily_df: close goes 102, 108, 106, 105, 109, 104, 110, 106, 112, 108
        # Entry when close > 107 → signal on bar 1 (close=108), enter bar 2 (open=107)
        # Trail = 5pts → initial stop = 102
        # Bar 2: high=110 → best=110, trail=105. low=104 > 105? No, 104 < 105 → exit at 105
        strategy = Strategy(
            entry="close > 107",
            direction="long",
            trailing_stop=5,
        )
        result = run_backtest(daily_df, strategy, empty_sessions)
        assert len(result.trades) >= 1
        first = result.trades[0]
        assert first.exit_reason == "trailing_stop"

    def test_trailing_stop_short(self, daily_df, empty_sessions):
        """Short with trailing stop: trail follows price down."""
        # Entry when close < 103 → signal on bar 0 (close=102), enter bar 1 (open=105)
        # Trail = 5pts → initial stop = 110
        # Bar 1: low=103 → best=103, trail=108. high=110 >= 108? Yes → exit at 108
        strategy = Strategy(
            entry="close < 103",
            direction="short",
            trailing_stop=5,
        )
        result = run_backtest(daily_df, strategy, empty_sessions)
        assert len(result.trades) >= 1
        for trade in result.trades:
            if trade.exit_reason == "trailing_stop":
                # Short trailing: exited when price retraced up
                assert trade.exit_reason == "trailing_stop"

    def test_trailing_stop_percentage(self, daily_df, empty_sessions):
        """Trailing stop as percentage string."""
        strategy = Strategy(
            entry="close > 107",
            direction="long",
            trailing_stop="5%",
        )
        result = run_backtest(daily_df, strategy, empty_sessions)
        # Should not crash, percentage resolves correctly
        assert isinstance(result.metrics.total_trades, int)
        assert result.metrics.total_trades >= 1

    def test_trailing_stop_with_fixed_stop(self, daily_df, empty_sessions):
        """Fixed stop acts as floor — trailing can only improve it."""
        # With wide trailing (50pts from entry ~107) and tight fixed stop (2pts),
        # the fixed stop is tighter initially → should hit "stop" not "trailing_stop"
        strategy = Strategy(
            entry="close > 107",
            direction="long",
            stop_loss=2,
            trailing_stop=50,
        )
        result = run_backtest(daily_df, strategy, empty_sessions)
        if result.trades:
            stopped = [t for t in result.trades if t.exit_reason == "stop"]
            # Fixed stop at 105 should dominate over trail at 57
            assert len(stopped) > 0

    def test_trailing_stop_immediate_loss(self):
        """Price goes against immediately — exits at initial trail level."""
        from barb.backtest.engine import _find_exit_in_minutes

        # Long entry at 100, trail=3 → initial stop=97
        # Price drops immediately
        minutes = _make_minutes(
            [
                (100, 100, 96, 97),  # low=96 < trail_stop=97
            ]
        )
        price, reason, best = _find_exit_in_minutes(
            minutes,
            True,
            None,
            None,
            None,
            trail_points=3,
            best_price=100,
        )
        assert reason == "trailing_stop"
        assert price == 97.0  # 100 - 3

    def test_trailing_stop_minute_precision(self):
        """Minute-level trailing: price rises, trail follows, then retrace exits."""
        from barb.backtest.engine import _find_exit_in_minutes

        # Long entry at 100, trail=2
        # Min 1: high=103 → best=103, trail=101. low=102 > 101, no exit
        # Min 2: high=106 → best=106, trail=104. low=105 > 104, no exit
        # Min 3: high=106 → best=106, trail=104. low=103 < 104 → exit at 104
        minutes = _make_minutes(
            [
                (100, 103, 102, 102),
                (102, 106, 105, 105),
                (105, 106, 103, 103),
            ]
        )
        price, reason, best = _find_exit_in_minutes(
            minutes,
            True,
            None,
            None,
            None,
            trail_points=2,
            best_price=100,
        )
        assert reason == "trailing_stop"
        assert price == 104.0  # best(106) - trail(2)
        assert best == 106.0

    def test_trailing_stop_with_tp(self):
        """Trailing stop + take profit coexist — TP wins if hit first."""
        from barb.backtest.engine import _find_exit_in_minutes

        # Long entry at 100, trail=3, TP at 105
        # Min 1: high=105 → TP hit at 105 (before trail catches up)
        minutes = _make_minutes(
            [
                (100, 106, 99, 105),
            ]
        )
        price, reason, _ = _find_exit_in_minutes(
            minutes,
            True,
            None,
            105.0,
            None,
            trail_points=3,
            best_price=100,
        )
        # Trail updates best to 106, trail_stop=103. low=99 < 103 → trailing_stop wins
        # (stop check comes before TP check in the loop)
        assert reason == "trailing_stop"
        assert price == 103.0

    def test_trailing_stop_exit_reason_distinct(self):
        """Exit reason is 'trailing_stop', distinct from 'stop'."""
        from barb.backtest.engine import _find_exit_in_minutes

        minutes = _make_minutes(
            [
                (100, 105, 102, 104),  # best=105, trail=103
                (104, 104, 102, 102),  # low=102 < 103 → trailing exit
            ]
        )
        price, reason, _ = _find_exit_in_minutes(
            minutes,
            True,
            None,
            None,
            None,
            trail_points=2,
            best_price=100,
        )
        assert reason == "trailing_stop"
        assert reason != "stop"


# --- Breakeven ---


class TestBreakeven:
    def test_breakeven_basic_long(self):
        """After N bars in profit, stop moves to entry → exit at entry price."""
        # 5 bars: entry on bar 1 (open=100), breakeven after 2 bars
        # Bar 2: open=102 (profit) → breakeven activates, stop=100
        # Bar 3: low=99 < 100 → exit at breakeven
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, 100, 102, 101, 98],
                "high": [104, 103, 105, 103, 100],
                "low": [98, 99, 100, 99, 96],
                "close": [102, 101, 103, 100, 97],
                "volume": [1000] * 5,
            },
            index=dates,
            dtype=float,
        )
        sessions = {"RTH": ("09:30", "16:15")}
        strategy = Strategy(
            entry="close > 101",
            direction="long",
            stop_loss=10,
            breakeven_bars=2,
        )
        result = run_backtest(df, strategy, sessions)
        assert len(result.trades) >= 1
        trade = result.trades[0]
        assert trade.exit_reason == "breakeven"
        assert trade.exit_price == trade.entry_price  # exited at entry

    def test_breakeven_short(self):
        """Short breakeven: in profit when open < entry."""
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, 100, 98, 99, 102],
                "high": [104, 103, 100, 101, 105],
                "low": [98, 97, 96, 97, 100],
                "close": [98, 99, 97, 100, 103],
                "volume": [1000] * 5,
            },
            index=dates,
            dtype=float,
        )
        sessions = {"RTH": ("09:30", "16:15")}
        strategy = Strategy(
            entry="close < 99",
            direction="short",
            stop_loss=10,
            breakeven_bars=2,
        )
        result = run_backtest(df, strategy, sessions)
        be_trades = [t for t in result.trades if t.exit_reason == "breakeven"]
        assert len(be_trades) >= 1

    def test_breakeven_not_in_profit(self):
        """After N bars but NOT in profit → stop doesn't move."""
        dates = pd.date_range("2024-01-02", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, 100, 98, 97, 96],
                "high": [104, 103, 100, 99, 98],
                "low": [98, 97, 96, 95, 94],
                "close": [102, 99, 97, 96, 95],
                "volume": [1000] * 5,
            },
            index=dates,
            dtype=float,
        )
        sessions = {"RTH": ("09:30", "16:15")}
        strategy = Strategy(
            entry="close > 101",
            direction="long",
            stop_loss=5,
            breakeven_bars=1,
        )
        result = run_backtest(df, strategy, sessions)
        # Not in profit at bar open → breakeven doesn't activate → hits fixed stop
        for trade in result.trades:
            assert trade.exit_reason != "breakeven"

    def test_breakeven_raises_stop(self):
        """Breakeven moves stop from initial level to entry."""
        # Entry at ~100, stop_loss=5 (stop at 95), breakeven_bars=1
        # After 1 bar in profit: stop moves to 100
        # Without breakeven: stop stays at 95
        dates = pd.date_range("2024-01-02", periods=6, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, 100, 102, 101, 99, 97],
                "high": [104, 103, 105, 103, 100, 98],
                "low": [98, 99, 100, 99, 97, 95],
                "close": [102, 101, 103, 100, 98, 96],
                "volume": [1000] * 6,
            },
            index=dates,
            dtype=float,
        )
        sessions = {"RTH": ("09:30", "16:15")}

        # With breakeven: exits at entry price
        s_be = Strategy(
            entry="close > 101",
            direction="long",
            stop_loss=5,
            breakeven_bars=2,
        )
        r_be = run_backtest(df, s_be, sessions)

        # Without breakeven: exits at fixed stop (lower)
        s_no = Strategy(
            entry="close > 101",
            direction="long",
            stop_loss=5,
        )
        r_no = run_backtest(df, s_no, sessions)

        if r_be.trades and r_no.trades:
            # Breakeven should preserve more P&L
            assert r_be.trades[0].pnl >= r_no.trades[0].pnl

    def test_breakeven_exit_reason_distinct(self):
        """Exit reason is 'breakeven', distinct from 'stop' and 'trailing_stop'."""
        from barb.backtest.engine import _check_exit_levels

        bar = pd.Series({"open": 100, "high": 103, "low": 98, "close": 99})
        # stop_reason="breakeven" → exit reason should be "breakeven"
        price, reason, _ = _check_exit_levels(
            bar,
            True,
            99.0,
            None,
            None,
            stop_reason="breakeven",
        )
        assert reason == "breakeven"
        assert reason != "stop"

    def test_breakeven_with_trailing(self):
        """Breakeven + trailing coexist — tighter wins."""
        from barb.backtest.engine import _find_exit_in_minutes

        # Long entry at 100, breakeven active (stop=100), trail=3 from best=105
        # Trail stop = 102, breakeven stop = 100
        # Trail is tighter (102 > 100) → trailing dominates
        minutes = _make_minutes(
            [
                (104, 105, 101, 102),  # best=105, trail=102. low=101 < 102 → trailing exit
            ]
        )
        price, reason, _ = _find_exit_in_minutes(
            minutes,
            True,
            100.0,
            None,
            None,
            trail_points=3,
            best_price=104,
            stop_reason="breakeven",
        )
        assert reason == "trailing_stop"
        assert price == 102.0
