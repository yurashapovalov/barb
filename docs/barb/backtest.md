# Backtest (barb/backtest/)

Тестирование торговых стратегий на исторических данных. Пользователь описывает стратегию на естественном языке → Claude формирует `run_backtest` tool call → движок симулирует сделки бар за баром → результат с метриками и equity curve.

## Как работает

```
Пользователь: "Лонг когда RSI ниже 30, стоп 2%, тейк 3%, макс 5 дней"
    ↓
Claude пишет: "Тестирую стратегию RSI oversold..."
    ↓
Claude вызывает run_backtest({strategy: {entry: "rsi(close,14) < 30", ...}})
    ↓
Engine: session → period → resample → evaluate → simulate → metrics
    ↓
Результат: 53 trades, PF 1.32, equity curve
```

## Архитектура

```
barb/backtest/
  __init__.py      — exports Strategy, run_backtest
  strategy.py      — Strategy dataclass + resolve_level
  engine.py        — pipeline: filter → resample → evaluate → simulate
  metrics.py       — Trade, BacktestMetrics, BacktestResult, calculate_metrics

assistant/tools/
  backtest.py      — BACKTEST_TOOL schema + run_backtest_tool wrapper
```

Принцип тот же что и в Query Engine: `barb/backtest/` — чистый Python без зависимости от LLM. Можно использовать из CLI, тестов, ноутбуков. `assistant/tools/backtest.py` — тонкая обёртка для Claude.

## Strategy

```python
@dataclass
class Strategy:
    entry: str                      # "rsi(close, 14) < 30"
    direction: str                  # "long" | "short"
    exit_target: str | None = None  # expression → fixed target price
    stop_loss: float | str | None = None    # 20 (points) or "2%" (percentage)
    take_profit: float | str | None = None  # 50 (points) or "3%" (percentage)
    exit_bars: int | None = None    # force exit after N bars
    slippage: float = 0.0          # points per side
```

### Stop/Target: пункты vs проценты

31 инструмент — акции за $20 и NQ за 20000. Стоп в пунктах бессмысленно сравнивать. Оба формата:

- **Число** → пункты: `stop_loss: 20` = 20 пунктов от входа
- **Строка с %** → проценты: `stop_loss: "2%"` = 2% от цены входа

```python
def resolve_level(value: float | str, entry_price: float) -> float:
    if isinstance(value, str) and value.endswith("%"):
        return entry_price * float(value.rstrip("%")) / 100
    return float(value)
```

### exit_target

Expression, вычисляется ОДИН РАЗ при входе в сделку. Результат — фиксированная цена. Пример: `exit_target: "prev(close)"` для gap fill → при входе вычисляется close предыдущего бара → эта цена становится целью.

Вычисление: на сигнальном баре с 200 барами истории для индикаторов (`_calc_exit_target`).

## Engine Pipeline

`engine.py` → `run_backtest()`:

```
Минутный DataFrame
    ↓
1. filter_session(df, session, sessions)     — из barb/interpreter
2. filter_period(df, period)                 — из barb/interpreter
3. resample(df, "daily")                     — из barb/interpreter
4. evaluate(strategy.entry, daily, FUNCTIONS) — из barb/expressions
5. _simulate(daily, entry_mask, strategy)    — бар за баром
6. calculate_metrics(trades) + build_equity_curve(trades) — метрики и equity
    ↓
BacktestResult(trades, metrics, equity_curve)
```

Движок переиспользует session/period/resample из Query Engine. Expressions — те же что в `run_query` (RSI, SMA, gap, streak — все 106 функций доступны).

### Entry Logic

- Условие входа вычисляется на **дневных** барах (все OHLCV доступны)
- **Вход на open СЛЕДУЮЩЕГО бара** после сигнала — стандарт в бэктестинге
- Одна позиция одновременно — сигналы при открытой позиции пропускаются

```
Bar N:   entry condition = True (evaluated with full OHLCV of bar N)
Bar N+1: entry at open (adjusted for slippage)
```

### Exit Logic (по приоритету)

1. **Stop loss** — low (long) / high (short) пересекает стоп-цену
2. **Take profit** — high (long) / low (short) пересекает тейк-цену
3. **Exit target** — цена достигает target price
4. **Exit bars** — timeout, выход по close
5. **End of data** — принудительное закрытие на последнем баре

При проверке стопа/тейка на дневном баре: если оба могли сработать — стоп первый (conservative assumption). Реальные результаты могут быть лучше.

### Slippage

Фиксированное проскальзывание в пунктах на каждую сторону:

```
Long entry:  actual = open + slippage
Long exit:   actual = exit_price - slippage
Short entry: actual = open - slippage
Short exit:  actual = exit_price + slippage
```

### Same-Bar Exit

Если стоп/тейк/таргет срабатывает на баре входа — сделка закрывается в тот же бар с `bars_held = 0`. Проверяется сразу после входа.

## Data Structures

### Trade

```python
@dataclass
class Trade:
    entry_date: date            # datetime.date
    entry_price: float
    exit_date: date
    exit_price: float
    direction: str              # "long" | "short"
    pnl: float                  # points (after slippage)
    exit_reason: str            # "stop" | "take_profit" | "target" | "timeout" | "end"
    bars_held: int
```

### BacktestMetrics

```python
@dataclass
class BacktestMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float             # процент (0-100)
    profit_factor: float        # gross_profit / abs(gross_loss), inf если нет losses
    avg_win: float              # points
    avg_loss: float             # points (отрицательное)
    max_drawdown: float         # points (peak to trough)
    total_pnl: float            # points
    expectancy: float           # avg pnl per trade
    avg_bars_held: float
    max_consecutive_wins: int
    max_consecutive_losses: int
```

### BacktestResult

```python
@dataclass
class BacktestResult:
    trades: list[Trade]
    metrics: BacktestMetrics
    equity_curve: list[float]   # cumulative P&L after each trade
```

## Tool Integration

`assistant/tools/backtest.py`:

### BACKTEST_TOOL

Tool schema для Claude. Описание с примерами стратегий (RSI, gap fade, trend following). Все поля strategy с типами. `session`, `period`, `title` — top-level.

### run_backtest_tool()

Обёртка: dict → Strategy → `run_backtest()` → сериализация.

Критический момент — **datetime.date → ISO string**. Trade.entry_date/exit_date — `datetime.date` объекты из engine. SSE (`json.dumps`) и Supabase (JSONB) требуют строки. Конвертация в wrapper:

```python
trades = [
    {
        "entry_date": str(t.entry_date),  # "2024-01-15"
        "exit_date": str(t.exit_date),
        ...
    }
    for t in result.trades
]
```

Возвращает:

```python
{
    "model_response": "Backtest: 53 trades | Win Rate 49.1% | PF 1.32 | ...",
    "backtest": {
        "type": "backtest",
        "title": "RSI Mean Reversion",
        "strategy": {entry, direction, stop_loss, ...},
        "metrics": {total_trades, win_rate, profit_factor, ...},
        "trades": [{entry_date, exit_date, pnl, exit_reason, ...}],
        "equity_curve": [52.5, 17.8, ...],
    },
}
```

### Формат для модели

Компактная строка:

```
Backtest: 53 trades | Win Rate 49.1% | PF 1.32 | Total +1087.0 pts | Max DD 1675.7 pts
Avg win: +171.2 | Avg loss: -124.6 | Avg bars: 1.1 | Consec W/L: 5/6
```

0 сделок: `Backtest: 0 trades — entry condition never triggered in this period.`

## Chat Dispatch

`assistant/chat.py` — `Assistant` class:

```python
tools=[BARB_TOOL, BACKTEST_TOOL]

# Dispatch по tu["name"]
if tu["name"] == "run_backtest":
    model_response, block = self._exec_backtest(tu["input"], title)
else:
    model_response, block = self._exec_query(tu["input"], title)
```

`_exec_query()` и `_exec_backtest()` — извлечённые методы. Оба возвращают `(model_response, block)`. Общий dispatch loop обрабатывает tool_start/tool_end, error handling, data_block events.

Backtest всегда использует `df_minute` — engine сам ресемплит в daily.

## SSE Events

Бэктест интегрируется в существующий SSE поток:

```
event: tool_start
data: {"tool_name": "run_backtest", "input": {"strategy": {...}, "title": "..."}}

event: data_block
data: {"type": "backtest", "title": "...", "strategy": {...}, "metrics": {...}, "trades": [...], "equity_curve": [...]}

event: tool_end
data: {"tool_name": "run_backtest", "duration_ms": 450, "error": null}
```

### Дискриминация типов

Query блоки — нет поля `type`. Backtest блоки — `type: "backtest"`. Frontend различает по наличию поля `type`.

### Хранение в DB

Блоки хранятся в `message.data` (JSONB[]). Тип определяется по полю `type`. Миграция не нужна — JSONB принимает любую структуру.

## System Prompt

Правило #9 в `<behavior>`:

```
9. Strategy testing → call run_backtest. Always include stop_loss (suggest 1-2% if user didn't specify).
   After results: comment on win rate, profit factor, and max drawdown.
   If 0 trades — explain why condition may be too restrictive.
```

## Design Decisions

| Решение | Почему |
|---------|--------|
| Entry на open следующего бара | Условия часто используют close, который известен только по завершении бара |
| Conservative assumption (стоп первый) | При неопределённости на дневном баре — пессимистичная оценка |
| Одна позиция одновременно | Простота. Position sizing — v2 |
| Дневные бары (не минутные) для симуляции | x100 быстрее. Минутная симуляция стопов — v2 |
| Slippage default 0 | Не навязываем, но Claude может предложить |
| Expressions = те же что run_query | 106 функций переиспользуются. Не нужен отдельный expression language |

## Тесты

`tests/test_backtest.py` — 28 тестов:

- **TestStrategy** — dataclass creation
- **TestResolveLevel** — points, percentage conversion
- **TestMetrics** — calculate_metrics, build_equity_curve, edge cases (0 trades, all wins, all losses)
- **TestEngineBasic** — синтетические данные (10-day predictable OHLCV), entry/exit logic, slippage, exit_bars timeout, same-bar exit
- **TestEngineRealData** — реальные NQ minute данные, RSI strategy, period filter, 0 trades case

```bash
.venv/bin/pytest tests/test_backtest.py -v
```

## File Structure

```
barb/backtest/
  __init__.py         — exports Strategy, run_backtest
  strategy.py         — Strategy dataclass, resolve_level()
  engine.py           — run_backtest(), _simulate(), _check_exit()
  metrics.py          — Trade, BacktestMetrics, BacktestResult, calculate_metrics()

assistant/tools/
  backtest.py         — BACKTEST_TOOL schema, run_backtest_tool(), _format_summary()

tests/
  test_backtest.py    — 28 tests (synthetic + real data)
```

### Dependencies

```
barb/backtest/engine.py  ← barb/backtest/strategy.py (Strategy, resolve_level)
                         ← barb/backtest/metrics.py (Trade, BacktestResult, calculate_metrics)
                         ← barb/expressions (evaluate)
                         ← barb/functions (FUNCTIONS)
                         ← barb/interpreter (filter_session, filter_period, resample, QueryError)

assistant/tools/backtest.py ← barb/backtest/engine (run_backtest)
                            ← barb/backtest/strategy (Strategy)
                            ← barb/backtest/metrics (BacktestMetrics)

assistant/chat.py ← assistant/tools/backtest (BACKTEST_TOOL, run_backtest_tool)
```
