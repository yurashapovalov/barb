# Backtest Module

## Overview

Backtest module allows traders to test trading strategies on historical data without writing code. The user describes a strategy in natural language, and the system simulates trades and returns performance metrics.

## User Experience

```
User: "Протестируй стратегию: шорт на гэпах вверх >50, стоп 20, тейк на gap fill. 2024 год."

Barb: Тестирую стратегию на гэпах вверх...

[Strategy Results Card]
Trades: 93
Win Rate: 47.3%
Profit Factor: 1.31
Avg Win: 42.5 pts
Avg Loss: -20.0 pts
Max Drawdown: -156 pts
Total P&L: +847 pts

[Trades Table - expandable]
```

## Architecture

```
barb/
  backtest/
    __init__.py
    engine.py      # Core backtest loop
    strategy.py    # Strategy dataclass
    metrics.py     # Performance calculations

assistant/
  tools/
    backtest.py    # LLM tool wrapper
```

### Separation of Concerns

- `barb/backtest/` — pure Python, no LLM dependency
- Can be used from CLI, API, tests, notebooks
- `assistant/tools/backtest.py` — thin wrapper for Claude

## Strategy Definition

```python
@dataclass
class Strategy:
    entry: str              # Expression: "gap > 50"
    direction: str          # "long" | "short"
    exit_target: str | None # Expression: "prev(close)" or None
    stop_loss: float | None # Points or None
    take_profit: float | None # Points or None
    exit_bars: int | None   # Max bars in trade or None
```

## Tool Schema

```python
BACKTEST_TOOL = {
    "name": "run_backtest",
    "description": """Test a trading strategy on historical data.

Returns list of simulated trades with entry/exit prices and performance metrics.
Use expressions from run_query for entry/exit conditions.
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "strategy": {
                "type": "object",
                "properties": {
                    "entry": {
                        "type": "string",
                        "description": "Entry condition expression, e.g. 'gap > 50'"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["long", "short"],
                        "description": "Trade direction"
                    },
                    "exit_target": {
                        "type": "string",
                        "description": "Exit price expression, e.g. 'prev(close)' for gap fill"
                    },
                    "stop_loss": {
                        "type": "number",
                        "description": "Stop loss in points"
                    },
                    "take_profit": {
                        "type": "number",
                        "description": "Take profit in points"
                    },
                    "exit_bars": {
                        "type": "integer",
                        "description": "Exit after N bars if no stop/target hit"
                    }
                },
                "required": ["entry", "direction"]
            },
            "period": {
                "type": "string",
                "description": "Date filter: '2024', '2024-01:2024-06', etc."
            },
            "session": {
                "type": "string",
                "enum": ["RTH", "ETH"],
                "description": "Trading session"
            },
            "title": {
                "type": "string",
                "description": "Short title for results card"
            }
        },
        "required": ["strategy", "title"]
    }
}
```

## Engine Logic

```python
def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    sessions: dict,
    session: str = "RTH",
    period: str | None = None,
) -> BacktestResult:
    """
    1. Filter data by session/period
    2. Resample to daily (entry on daily bars)
    3. Evaluate entry expression → entry signals
    4. For each entry signal:
       - Record entry price (open of signal bar or next bar)
       - Simulate exit based on stop/target/expression
       - Record exit price and P&L
    5. Calculate metrics from trades
    """
```

### Entry Logic

- Entry condition evaluated on daily bars
- Entry price = open of the bar where condition is true
- One trade at a time (no overlapping positions)

### Exit Logic (priority order)

1. **Stop loss hit** — if low (long) or high (short) crosses stop price
2. **Take profit hit** — if high (long) or low (short) crosses target price
3. **Exit expression** — if expression becomes true
4. **Exit bars** — max duration reached
5. **End of data** — force close at last bar

### Intraday Simulation

For accurate stop/target simulation on daily bars:
- Check if stop OR target could be hit within the bar
- Use high/low to determine which was hit first
- Assumption: if both possible, stop hit first (conservative)

## Metrics

```python
@dataclass
class BacktestMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float           # winning / total
    profit_factor: float      # gross_profit / gross_loss
    avg_win: float            # points
    avg_loss: float           # points
    max_drawdown: float       # points (peak to trough)
    total_pnl: float          # points
    expectancy: float         # avg pnl per trade
```

## Result Structure

```python
@dataclass
class BacktestResult:
    trades: list[Trade]       # Individual trades
    metrics: BacktestMetrics  # Aggregate stats
    equity_curve: list[float] # Cumulative P&L after each trade
```

```python
@dataclass
class Trade:
    entry_date: date
    entry_price: float
    exit_date: date
    exit_price: float
    direction: str            # "long" | "short"
    pnl: float                # points
    exit_reason: str          # "stop" | "target" | "expression" | "timeout" | "end"
```

## Frontend Display

### Strategy Results Card

Shows key metrics at a glance:
- Trades count, win rate
- Profit factor, expectancy
- Total P&L, max drawdown

### Trades Table (expandable)

| Date | Direction | Entry | Exit | P&L | Exit Reason |
|------|-----------|-------|------|-----|-------------|
| 2024-01-15 | Short | 18450 | 18400 | +50 | target |
| 2024-01-22 | Short | 18200 | 18220 | -20 | stop |

### Equity Curve (optional, v2)

Line chart showing cumulative P&L over time.

## Examples

### Gap Fill Strategy

```
"Шорт на гэпах вверх >50 пунктов, тейк на закрытии гэпа, стоп 20"

→ run_backtest({
    strategy: {
      entry: "open - prev(close) > 50",
      direction: "short",
      exit_target: "prev(close)",
      stop_loss: 20
    },
    period: "2024",
    session: "RTH"
  })
```

### Reversal After Big Down Day

```
"Лонг после дней с падением >2.5%, тейк 1%, стоп 0.5%"

→ run_backtest({
    strategy: {
      entry: "(prev(close) - prev(open)) / prev(open) < -0.025",
      direction: "long",
      take_profit: "open * 0.01",  // 1% from entry
      stop_loss: "open * 0.005"    // 0.5% from entry
    },
    period: "2024",
    session: "RTH"
  })
```

### Friday Reversal

```
"Шорт в пятницу если неделя выросла >3%, держать до конца дня"

→ run_backtest({
    strategy: {
      entry: "dayofweek() == 4 and (close - prev(close, 5)) / prev(close, 5) > 0.03",
      direction: "short",
      exit_bars: 1
    },
    period: "2024",
    session: "RTH"
  })
```

## Implementation Plan

### Phase 1: Core Engine
- [ ] `barb/backtest/strategy.py` — Strategy dataclass
- [ ] `barb/backtest/engine.py` — Basic backtest loop
- [ ] `barb/backtest/metrics.py` — Metrics calculation
- [ ] Unit tests with known outcomes

### Phase 2: Tool Integration
- [ ] `assistant/tools/backtest.py` — Tool wrapper
- [ ] Update system prompt with backtest instructions
- [ ] Add examples to prompt

### Phase 3: Frontend
- [ ] Strategy results card component
- [ ] Trades table (expandable)
- [ ] SSE events for backtest progress

### Phase 4: Enhancements
- [ ] Equity curve visualization
- [ ] Multiple strategies comparison
- [ ] Position sizing options
- [ ] Commission/slippage modeling

## Open Questions

1. **Entry timing**: Open of signal bar vs open of next bar?
2. **Percentage vs points**: Support both for stop/target?
3. **Multiple timeframes**: Entry on daily, exit on intraday?
4. **Equity curve**: Calculate and display in v1 or defer?
