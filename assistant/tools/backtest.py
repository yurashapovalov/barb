"""Backtest tool for Anthropic Claude."""

from collections import defaultdict

import pandas as pd

from barb.backtest.engine import run_backtest
from barb.backtest.metrics import BacktestResult
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
- commission: points per round-trip, default 0

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
                    "commission": {
                        "type": "number",
                        "description": "Commission in points per round-trip, default 0",
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
        commission=strat.get("commission", 0.0),
    )

    result = run_backtest(
        df_minute,
        strategy,
        sessions,
        session=input_data.get("session"),
        period=input_data.get("period"),
    )

    return {
        "model_response": _format_summary(result),
        "result": result,
    }


def _build_backtest_card(result: BacktestResult, title: str) -> dict:
    """Build typed DataCard from BacktestResult.

    Returns {title, blocks: [metrics-grid, area-chart, horizontal-bar, table]}.
    """
    m = result.metrics

    if m.total_trades == 0:
        return {
            "title": title,
            "blocks": [
                {
                    "type": "metrics-grid",
                    "items": [{"label": "Trades", "value": "0"}],
                },
            ],
        }

    pf = f"{m.profit_factor:.2f}" if m.profit_factor != float("inf") else "inf"
    rf = f"{m.recovery_factor:.2f}" if m.recovery_factor != float("inf") else "inf"
    pnl_color = "green" if m.total_pnl > 0 else "red" if m.total_pnl < 0 else None

    # 1. metrics-grid
    items = [
        {"label": "Trades", "value": str(m.total_trades)},
        {"label": "Win Rate", "value": f"{m.win_rate:.1f}%"},
        {"label": "PF", "value": pf},
        {"label": "Total P&L", "value": f"{m.total_pnl:+,.1f}"},
        {"label": "Avg Win", "value": f"{m.avg_win:+,.1f}"},
        {"label": "Avg Loss", "value": f"{m.avg_loss:,.1f}"},
        {"label": "Max DD", "value": f"{m.max_drawdown:,.1f}"},
        {"label": "Recovery", "value": rf},
    ]
    if pnl_color:
        items[3]["color"] = pnl_color

    metrics_block = {"type": "metrics-grid", "items": items}

    # 2. area-chart — equity + drawdown
    equity = 0.0
    peak = 0.0
    chart_data = []
    for t in result.trades:
        equity += t.pnl
        peak = max(peak, equity)
        chart_data.append(
            {
                "date": str(t.exit_date),
                "equity": round(equity, 2),
                "drawdown": round(equity - peak, 2),
            }
        )

    area_block = {
        "type": "area-chart",
        "x_key": "date",
        "series": [
            {"key": "equity", "label": "Equity", "style": "line"},
            {"key": "drawdown", "label": "Drawdown", "style": "area", "color": "red"},
        ],
        "data": chart_data,
    }

    # 3. horizontal-bar — exit type breakdown
    exits = defaultdict(lambda: {"pnl": 0.0, "count": 0, "wins": 0, "losses": 0})
    for t in result.trades:
        exits[t.exit_reason]["pnl"] += t.pnl
        exits[t.exit_reason]["count"] += 1
        if t.pnl > 0:
            exits[t.exit_reason]["wins"] += 1
        else:
            exits[t.exit_reason]["losses"] += 1

    exit_items = [
        {
            "label": reason.replace("_", " ").title(),
            "value": round(d["pnl"], 1),
            "detail": f"{d['count']} trades (W:{d['wins']} L:{d['losses']})",
        }
        for reason, d in sorted(exits.items(), key=lambda x: x[1]["pnl"], reverse=True)
    ]

    hbar_block = {"type": "horizontal-bar", "items": exit_items}

    # 4. table — all trades
    trade_rows = [
        {
            "entry_date": str(t.entry_date),
            "exit_date": str(t.exit_date),
            "direction": t.direction,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "pnl": round(t.pnl, 2),
            "exit_reason": t.exit_reason,
            "bars_held": t.bars_held,
        }
        for t in result.trades
    ]

    table_block = {
        "type": "table",
        "columns": [
            "entry_date",
            "exit_date",
            "direction",
            "entry_price",
            "exit_price",
            "pnl",
            "exit_reason",
            "bars_held",
        ],
        "rows": trade_rows,
    }

    card_title = f"{title} · {m.total_trades} trades"
    return {
        "title": card_title,
        "blocks": [metrics_block, area_block, hbar_block, table_block],
    }


def _format_summary(result: BacktestResult) -> str:
    """Format backtest result into 5-line summary for model analysis."""
    m = result.metrics

    if m.total_trades == 0:
        return "Backtest: 0 trades — entry condition never triggered in this period."

    pf = f"{m.profit_factor:.2f}" if m.profit_factor != float("inf") else "inf"
    rf = f"{m.recovery_factor:.2f}" if m.recovery_factor != float("inf") else "inf"

    # Line 1: headline metrics
    line1 = (
        f"Backtest: {m.total_trades} trades | "
        f"Win Rate {m.win_rate:.1f}% | PF {pf} | "
        f"Total {m.total_pnl:+.1f} pts | Max DD {m.max_drawdown:.1f} pts"
    )

    # Line 2: trade-level stats
    sorted_pnls = sorted((t.pnl for t in result.trades), reverse=True)
    best = sorted_pnls[0]
    worst = sorted_pnls[-1]
    line2 = (
        f"Avg win: {m.avg_win:+.1f} | Avg loss: {m.avg_loss:.1f} | "
        f"Best: {best:+.1f} | Worst: {worst:+.1f} | "
        f"Avg bars: {m.avg_bars_held:.1f} | Recovery: {rf} | "
        f"Consec W/L: {m.max_consecutive_wins}/{m.max_consecutive_losses}"
    )

    # Line 3: yearly breakdown from trades
    yearly = defaultdict(lambda: {"pnl": 0.0, "count": 0})
    for t in result.trades:
        year = t.entry_date.year if hasattr(t.entry_date, "year") else int(str(t.entry_date)[:4])
        yearly[year]["pnl"] += t.pnl
        yearly[year]["count"] += 1
    parts = [f"{y} {d['pnl']:+.1f} ({d['count']})" for y, d in sorted(yearly.items())]
    line3 = f"By year: {' | '.join(parts)}"

    # Line 4: exit type P&L breakdown with win/loss counts
    exits = defaultdict(lambda: {"pnl": 0.0, "count": 0, "wins": 0, "losses": 0})
    for t in result.trades:
        exits[t.exit_reason]["pnl"] += t.pnl
        exits[t.exit_reason]["count"] += 1
        if t.pnl > 0:
            exits[t.exit_reason]["wins"] += 1
        else:
            exits[t.exit_reason]["losses"] += 1
    exit_parts = [
        f"{r} {d['count']} (W:{d['wins']} L:{d['losses']}, {d['pnl']:+.1f})"
        for r, d in sorted(exits.items())
    ]
    line4 = f"Exits: {' | '.join(exit_parts)}"

    # Line 5: concentration — top 3 trades as % of total PnL
    top3_pnl = sum(sorted_pnls[:3])
    if m.total_pnl != 0:
        top3_pct = abs(top3_pnl / m.total_pnl) * 100
        line5 = f"Top 3 trades: {top3_pnl:+.1f} pts ({top3_pct:.1f}% of total PnL)"
    else:
        line5 = f"Top 3 trades: {top3_pnl:+.1f} pts"

    return f"{line1}\n{line2}\n{line3}\n{line4}\n{line5}"
