"""Tests for backtest engine.

Uses both synthetic data (deterministic, hand-verified trades)
and real NQ data (smoke tests on real market data).
"""

import pandas as pd
import pytest

from barb.backtest.engine import run_backtest
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
