"""Trade results and performance metrics."""

from dataclasses import dataclass
from datetime import date


@dataclass
class Trade:
    entry_date: date
    entry_price: float
    exit_date: date
    exit_price: float
    direction: str  # "long" | "short"
    pnl: float  # points (after slippage)
    exit_reason: str  # "stop" | "target" | "take_profit" | "timeout" | "end"
    bars_held: int


@dataclass
class BacktestMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float  # gross_profit / abs(gross_loss), inf if no losses
    avg_win: float  # points
    avg_loss: float  # points
    max_drawdown: float  # points (peak to trough of equity curve)
    total_pnl: float  # points
    expectancy: float  # avg pnl per trade
    avg_bars_held: float
    max_consecutive_wins: int
    max_consecutive_losses: int


@dataclass
class BacktestResult:
    trades: list[Trade]
    metrics: BacktestMetrics
    equity_curve: list[float]  # cumulative P&L after each trade


def calculate_metrics(trades: list[Trade]) -> BacktestMetrics:
    """Calculate performance metrics from a list of trades."""
    if not trades:
        return BacktestMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            profit_factor=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            max_drawdown=0.0,
            total_pnl=0.0,
            expectancy=0.0,
            avg_bars_held=0.0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
        )

    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]

    gross_profit = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))

    # Equity curve + max drawdown
    equity = []
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cumulative += t.pnl
        equity.append(cumulative)
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    # Consecutive wins/losses
    max_consec_wins = 0
    max_consec_losses = 0
    current_wins = 0
    current_losses = 0
    for t in trades:
        if t.pnl > 0:
            current_wins += 1
            current_losses = 0
            if current_wins > max_consec_wins:
                max_consec_wins = current_wins
        else:
            current_losses += 1
            current_wins = 0
            if current_losses > max_consec_losses:
                max_consec_losses = current_losses

    total = len(trades)
    return BacktestMetrics(
        total_trades=total,
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=len(wins) / total * 100 if total else 0.0,
        profit_factor=gross_profit / gross_loss if gross_loss > 0 else float("inf"),
        avg_win=gross_profit / len(wins) if wins else 0.0,
        avg_loss=-gross_loss / len(losses) if losses else 0.0,
        max_drawdown=max_dd,
        total_pnl=cumulative,
        expectancy=cumulative / total if total else 0.0,
        avg_bars_held=sum(t.bars_held for t in trades) / total if total else 0.0,
        max_consecutive_wins=max_consec_wins,
        max_consecutive_losses=max_consec_losses,
    )


def build_equity_curve(trades: list[Trade]) -> list[float]:
    """Build cumulative P&L curve from trades."""
    curve = []
    cumulative = 0.0
    for t in trades:
        cumulative += t.pnl
        curve.append(round(cumulative, 4))
    return curve
