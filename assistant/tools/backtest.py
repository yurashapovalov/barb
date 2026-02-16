"""Backtest tool for Anthropic Claude."""

from dataclasses import asdict

import pandas as pd

from barb.backtest.engine import run_backtest
from barb.backtest.metrics import BacktestMetrics
from barb.backtest.strategy import Strategy

BACKTEST_TOOL = {
    "name": "run_backtest",
    "description": """Test a trading strategy on historical data.

Simulates trades bar-by-bar on daily data and returns performance metrics.
Uses the same expression syntax as run_query for entry/exit conditions.

Strategy fields:
- entry: boolean expression that triggers a trade (e.g. "rsi(close, 14) < 30")
- direction: "long" or "short"
- stop_loss: points (number) or percentage (string "2%"). Distance from entry.
- take_profit: points (number) or percentage (string "3%"). Distance from entry.
- exit_target: expression evaluated ONCE at entry → fixed target price
  (e.g. "prev(close)" for gap fill)
- exit_bars: force exit after N bars if no stop/target hit
- slippage: points per side, default 0

Entry: signal on bar N → enter at bar N+1's open.
Exit priority: stop → take_profit → exit_target → exit_bars timeout → end of data.

<patterns>
Common entry patterns:
  N consecutive red candles   → streak(red()) >= N (each bar: close < open)
  N consecutive falling days  → streak(close < prev(close)) >= N (each close lower than previous)
  price below last N closes   → falling(close, N) (current close below ALL of last N)
  gap up                      → open - prev(close) > 0
  gap down                    → prev(close) - open > 0
  inside day                  → high < prev(high) and low > prev(low)
  NR7 (narrowest range 7d)    → range() == rolling_min(range(), 7)
  above moving average        → close > sma(close, 200)
  oversold bounce             → rsi(close, 14) < 30
  breakout                    → close > rolling_max(high, 20)
</patterns>

<examples>
Example 1 — RSI oversold mean reversion:
User: "Протестируй лонг когда RSI ниже 30, стоп 2%, тейк 3%, макс 5 дней"
→ run_backtest(strategy={"entry": "rsi(close, 14) < 30", "direction": "long",
    "stop_loss": "2%", "take_profit": "3%", "exit_bars": 5},
    session="RTH", title="RSI < 30 Long")

Example 2 — gap fade with target:
User: "Шорт после гэпа вверх >50 пунктов, тейк на вчерашний клоуз, стоп 20"
→ run_backtest(strategy={"entry": "open - prev(close) > 50", "direction": "short",
    "exit_target": "prev(close)", "stop_loss": 20},
    session="RTH", period="2024", title="Gap Fade Short >50")

Example 3 — trend following:
User: "Покупка когда цена выше 200 SMA и откатилась ниже 21 EMA, стоп 1.5%"
→ run_backtest(strategy={"entry": "close > sma(close, 200) and close < ema(close, 21)",
    "direction": "long", "stop_loss": "1.5%", "take_profit": "3%", "exit_bars": 10},
    session="RTH", title="EMA Pullback in Uptrend")
</examples>""",
    "input_schema": {
        "type": "object",
        "properties": {
            "strategy": {
                "type": "object",
                "properties": {
                    "entry": {
                        "type": "string",
                        "description": "Entry condition expression",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["long", "short"],
                    },
                    "exit_target": {
                        "type": "string",
                        "description": "Expression evaluated once at entry → fixed target price",
                    },
                    "stop_loss": {
                        "description": "Number = points, string = percentage ('2%')",
                    },
                    "take_profit": {
                        "description": "Number = points, string = percentage ('3%')",
                    },
                    "exit_bars": {
                        "type": "integer",
                        "description": "Force exit after N bars",
                    },
                    "slippage": {
                        "type": "number",
                        "description": "Slippage in points per side, default 0",
                    },
                },
                "required": ["entry", "direction"],
            },
            "session": {
                "type": "string",
                "enum": ["RTH", "ETH"],
                "description": "Trading session filter",
            },
            "period": {
                "type": "string",
                "description": "Date filter: '2024', '2024-01:2024-06', etc.",
            },
            "title": {
                "type": "string",
                "description": "Short title for results card (user's language)",
            },
        },
        "required": ["strategy", "title"],
    },
}


def run_backtest_tool(
    input_data: dict,
    df_minute: pd.DataFrame,
    sessions: dict,
) -> dict:
    """Execute backtest and return structured result.

    Returns dict with:
        - model_response: compact summary for model
        - backtest: full data for UI (metrics, trades, equity_curve, strategy)
    """
    strat = input_data["strategy"]
    strategy = Strategy(
        entry=strat["entry"],
        direction=strat["direction"],
        exit_target=strat.get("exit_target"),
        stop_loss=strat.get("stop_loss"),
        take_profit=strat.get("take_profit"),
        exit_bars=strat.get("exit_bars"),
        slippage=strat.get("slippage", 0.0),
    )

    result = run_backtest(
        df_minute,
        strategy,
        sessions,
        session=input_data.get("session"),
        period=input_data.get("period"),
    )

    # Convert datetime.date → ISO string for JSON serialization.
    # Trade.entry_date/exit_date are datetime.date from engine.
    trades = [
        {
            "entry_date": str(t.entry_date),
            "exit_date": str(t.exit_date),
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "direction": t.direction,
            "pnl": t.pnl,
            "exit_reason": t.exit_reason,
            "bars_held": t.bars_held,
        }
        for t in result.trades
    ]

    return {
        "model_response": _format_summary(result.metrics),
        "backtest": {
            "type": "backtest",
            "title": input_data.get("title", "Backtest"),
            "strategy": asdict(strategy),
            "metrics": asdict(result.metrics),
            "trades": trades,
            "equity_curve": result.equity_curve,
        },
    }


def _format_summary(m: BacktestMetrics) -> str:
    """Format backtest metrics into compact string for model."""
    if m.total_trades == 0:
        return "Backtest: 0 trades — entry condition never triggered in this period."

    pf = f"{m.profit_factor:.2f}" if m.profit_factor != float("inf") else "inf"
    return (
        f"Backtest: {m.total_trades} trades | "
        f"Win Rate {m.win_rate:.1f}% | PF {pf} | "
        f"Total {m.total_pnl:+.1f} pts | Max DD {m.max_drawdown:.1f} pts\n"
        f"Avg win: {m.avg_win:+.1f} | Avg loss: {m.avg_loss:.1f} | "
        f"Avg bars: {m.avg_bars_held:.1f} | "
        f"Consec W/L: {m.max_consecutive_wins}/{m.max_consecutive_losses}"
    )
