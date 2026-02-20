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
Tool: session → period → Engine: resample → minute index → evaluate → simulate → metrics
    ↓
Результат: 53 trades, PF 1.32, equity curve
```

## Архитектура

```
barb/backtest/
  __init__.py      — exports Strategy, run_backtest
  strategy.py      — Strategy dataclass + resolve_level
  engine.py        — pipeline: validate → resample → minute index → evaluate → simulate
  metrics.py       — Trade, BacktestMetrics, BacktestResult, calculate_metrics

assistant/tools/
  backtest.py      — BACKTEST_TOOL schema + run_backtest_tool wrapper
```

Принцип тот же что и в Query Engine: `barb/backtest/` — чистый Python без зависимости от LLM. Можно использовать из CLI, тестов, ноутбуков. `assistant/tools/backtest.py` — тонкая обёртка для Claude.

## Strategy

```python
@dataclass
class Strategy:
    entry: str                              # "rsi(close, 14) < 30"
    direction: str                          # "long" | "short"
    exit_target: str | None = None          # expression → fixed target price
    stop_loss: float | str | None = None    # 20 (points) or "2%" (percentage)
    take_profit: float | str | None = None  # 50 (points) or "3%" (percentage)
    trailing_stop: float | str | None = None  # trail distance (points or "1.5%")
    breakeven_bars: int | None = None       # after N bars in profit, move stop to entry
    exit_bars: int | None = None            # force exit after N bars
    slippage: float = 0.0                   # points per side
    commission: float = 0.0                 # points per round-trip
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

`engine.py` → `run_backtest(df, strategy, timeframe="daily")`:

```
Pre-filtered DataFrame (session/period filtering done by caller)
    ↓
1. Validate timeframe (allowed: 5m, 15m, 30m, 1h, 2h, 4h, daily)
2. resample(df, timeframe)                          — из barb/interpreter
3. _build_minute_index(df, bars)                    — map bar → minute rows (searchsorted, O(m log n))
4. evaluate(strategy.entry, bars, FUNCTIONS)         — из barb/expressions
5. _simulate(bars, entry_mask, strategy, minute_by_bar) — бар за баром
6. calculate_metrics(trades) + build_equity_curve(trades)
    ↓
BacktestResult(trades, metrics, equity_curve)
```

**Разделение ответственности**: engine получает уже отфильтрованные данные. Session/period filtering — задача tool wrapper (`assistant/tools/backtest.py`). Engine только resample + simulate.

Timeframes: `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `daily`. 1m excluded (millions of bars, pointless exit resolution). Weekly+ excluded (too few bars).

Expressions — те же что в `run_query` (RSI, SMA, gap, streak — все 106 функций доступны).

### Entry Logic

- Условие входа вычисляется на барах выбранного timeframe (все OHLCV доступны)
- **Вход на open СЛЕДУЮЩЕГО бара** после сигнала — стандарт в бэктестинге
- Одна позиция одновременно — сигналы при открытой позиции пропускаются

```
Bar N:   entry condition = True (evaluated with full OHLCV of bar N)
Bar N+1: entry at open (adjusted for slippage)
```

### Exit Logic

Два уровня разрешения: минутный (точный) и дневной (fallback).

**Минутный уровень** (когда есть минутные данные):

Движок проходит по минутным барам дня хронологически и проверяет на каждом баре:
1. **Stop loss** — low (long) / high (short) пересекает стоп-цену
2. **Take profit** — high (long) / low (short) пересекает тейк-цену
3. **Exit target** — цена достигает target price

Первый сработавший уровень = выход. Это устраняет conservative assumption — если TP сработал в 09:45, а стоп в 10:15, движок корректно фиксирует TP.

**Дневной уровень** (fallback, когда минутных данных нет):

Те же проверки на дневном баре. Приоритет: stop → take_profit → target. Если оба могли сработать на одном баре — стоп первый (conservative assumption).

**После price-based проверок** (оба уровня):
4. **Exit bars** — timeout, выход по close (считается в барах выбранного timeframe)
5. **End of data** — принудительное закрытие на последнем баре

```
_resolve_exit(daily_bar, day_minutes, ...)
    ├─ minute data available → _find_exit_in_minutes()  — walks chronologically
    └─ no minute data        → _check_exit_levels()     — conservative daily check
    then: timeout check (exit_bars)
```

### Slippage & Commission

Фиксированное проскальзывание в пунктах на каждую сторону:

```
Long entry:  actual = open + slippage
Long exit:   actual = exit_price - slippage
Short entry: actual = open - slippage
Short exit:  actual = exit_price + slippage
```

Commission — фиксированная в пунктах за round-trip, вычитается из P&L каждой сделки после slippage. Оба в тех же единицах что P&L (пункты).

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
    exit_reason: str            # "stop" | "take_profit" | "target" | "trailing_stop" | "breakeven" | "timeout" | "end"
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
    recovery_factor: float          # total_pnl / max_drawdown (inf if no drawdown)
    gross_profit: float             # sum of winning trade pnls
    gross_loss: float               # sum of losing trade pnls (negative number)
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

Tool schema для Claude. Описание с примерами стратегий (RSI, gap fade, trend following). Все поля strategy с типами. `from` (timeframe), `session`, `period`, `title` — top-level.

### run_backtest_tool()

Обёртка с data preparation: session/period filtering → Strategy → `run_backtest(df, strategy, timeframe)` → `BacktestResult`.

Data prep pipeline (before engine):
1. `filter_session(df, session, sessions)` — если указан session
2. `filter_period(df, period)` — если указан period
3. Передаёт timeframe (`from` field, default "daily") в engine

Возвращает:

```python
{
    "model_response": "Backtest: 53 trades | Win Rate 49.1% | PF 1.32 | ...",
    "result": BacktestResult,  # объект, не dict
}
```

### _build_backtest_card()

Конвертирует `BacktestResult` → typed data block для UI. Вызывается из `chat.py._exec_backtest()`.

datetime.date → ISO string конвертация происходит здесь (для JSON/SSE/Supabase).

Возвращает:

```python
{
    "title": "RSI < 30 Long · 71 trades",
    "blocks": [
        {"type": "metrics-grid", "items": [{"label": "Trades", "value": "71"}, ...]},
        {"type": "area-chart", "x_key": "date", "series": [...], "data": [...]},
        {"type": "horizontal-bar", "items": [{"label": "Take Profit", "value": 6106.1, "detail": "..."}]},
        {"type": "table", "columns": [...], "rows": [...]},
    ],
}
```

4 блока:
1. **metrics-grid** — 8 метрик (Trades, Win Rate, PF, Total P&L, Avg Win, Avg Loss, Max DD, Recovery). P&L с color (green/red).
2. **area-chart** — equity curve (line) + drawdown (area, red). Computed from trades, not from BacktestResult.equity_curve.
3. **horizontal-bar** — exit type breakdown, sorted by PnL desc. Detail: count + W/L.
4. **table** — all trades (entry_date, exit_date, direction, entry/exit price, pnl, exit_reason, bars_held).

0 сделок → single metrics-grid block с Trades=0.

### Формат для модели

5-строчная сводка — каждая строка служит для анализа Claude:

```
Backtest: 90 trades | Win Rate 52.2% | PF 1.48 | Total +2555.0 pts | Max DD 1675.7 pts
Avg win: +171.2 | Avg loss: -124.6 | Best: +302.2 | Worst: -339.5 | Avg bars: 1.1 | Recovery: 1.52 | Consec W/L: 4/7
By year: 2020 +1200.5 (25) | 2021 +408.2 (22) | 2022 -102.0 (18) | 2023 +893.1 (16) | 2024 +155.2 (9)
Exits: stop 43 (W:0 L:43, -1800.5) | take_profit 38 (W:38 L:0, +4200.0) | timeout 9 (W:5 L:4, +155.5)
Top 3 trades: +1850.0 pts (72.4% of total PnL)
```

- Line 1: headline metrics
- Line 2: trade-level stats (avg win/loss, best/worst, avg bars, recovery factor, max consecutive W/L)
- Line 3: yearly P&L breakdown — stability/regime dependency
- Line 4: exit type with W/L counts — reveals broken exit logic (e.g. target exits with losses)
- Line 5: concentration — dependency on outlier trades

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

Backtest всегда получает `df_minute`. Tool wrapper фильтрует session/period, engine ресемплит в нужный timeframe.

## SSE Events

Бэктест интегрируется в существующий SSE поток:

```
event: tool_start
data: {"tool_name": "run_backtest", "input": {"strategy": {...}, "title": "..."}}

event: data_block
data: {"title": "RSI < 30 Long · 71 trades", "blocks": [{type: "metrics-grid", ...}, {type: "area-chart", ...}, {type: "horizontal-bar", ...}, {type: "table", ...}]}

event: tool_end
data: {"tool_name": "run_backtest", "duration_ms": 450, "error": null}
```

### Единый формат

Query и backtest блоки используют одинаковый формат `{title, blocks: Block[]}`. Frontend проверяет наличие `title` + `blocks` через `isDataBlockEvent()`.

### Хранение в DB

Блоки хранятся в `message.data` (JSONB). Все блоки — `{title, blocks}`. JSONB принимает любую структуру.

## System Prompt

Правило #9 в `<behavior>`:

```
9. Strategy testing → call run_backtest. Always include stop_loss (suggest 1-2% if user didn't specify).
   After results — analyze strategy QUALITY, don't just repeat numbers:
   a) Yearly stability: consistent across years, or depends on one period?
   b) Exit analysis: which exit type drives profits? Are stops destroying gains?
   c) Concentration: if top 3 trades dominate total PnL — flag fragility.
   d) Trade count: below 30 trades = insufficient data, warn explicitly.
   e) Suggest one specific variation (tighter stop, trend filter, session filter).
   f) If PF > 2.0 or win rate > 70% — express skepticism, suggest stress testing.
   If 0 trades — explain why condition may be too restrictive and suggest relaxing it.
```

## Design Decisions

| Решение | Почему |
|---------|--------|
| Entry на open следующего бара | Условия часто используют close, который известен только по завершении бара |
| Минутки для exit, timeframe бары для entry | Entry evaluation на ресемплированных барах (быстро, все индикаторы). Exit resolution на минутных (точно, устраняет conservative assumption) |
| Fallback на бар timeframe | Синтетические тесты и данные без минуток → `_check_exit_levels()` с conservative assumption (стоп первый) |
| Tool wrapper = data prep, engine = simulation | Чистое разделение: engine не знает про sessions/periods. Tool wrapper фильтрует данные, engine ресемплит и считает |
| Timeframe validation whitelist | 1m excluded (millions of bars). Weekly+ excluded (too few bars, exit_bars semantics absurd) |
| Одна позиция одновременно | Простота. Position sizing — v2 |
| exit_bars в барах timeframe | Timeout считает бары выбранного timeframe. exit_bars=5 на 1h = 5 часовых баров |
| Slippage default 0 | Не навязываем, но Claude может предложить |
| Commission в пунктах | Те же единицы что P&L и slippage. Вычитается из P&L после slippage |
| Recovery Factor, не Sharpe | RF = profit per unit of pain, понятен трейдерам. Sharpe нужна annualization и % returns — Phase 2 |
| Expressions = те же что run_query | 106 функций переиспользуются. Не нужен отдельный expression language |

## Тесты

`tests/test_backtest.py` — 76 тестов:

- **TestStrategy** — dataclass creation
- **TestResolveLevel** — points, percentage conversion
- **TestMetrics** — calculate_metrics, build_equity_curve, edge cases (0 trades, all wins, all losses)
- **TestEngineBasic** — синтетические данные (10-day predictable OHLCV), entry/exit logic, slippage, exit_bars timeout, same-bar exit
- **TestEngineRealData** — реальные NQ minute данные (pre-filtered RTH), RSI strategy, period filter. Минутные данные → `_find_exit_in_minutes()`
- **TestFindExitInMinutes** — unit tests для минутного разрешения: stop first, TP first, both on same bar, no exit, target, short positions
- **TestResolveExit** — dispatch: минутки vs fallback, timeout после price check
- **TestMinuteResolutionIntegration** — integration test: одинаковые данные, разный результат с/без минуток
- **TestNewMetrics** — recovery_factor, gross_profit/gross_loss, edge cases
- **TestCommission** — commission reduces PnL, default zero, works with slippage
- **TestFormatSummary** — 5-line output, yearly breakdown, exit types, concentration, recovery factor
- **TestTrailingStop** — trailing stop: long/short, percentage, with fixed stop, minute precision
- **TestBreakeven** — breakeven: long/short, not-in-profit, raises stop, with trailing
- **TestTimeframe** — timeframe validation, daily default, 1h and 15m on real data, intraday vs daily trade count

```bash
.venv/bin/pytest tests/test_backtest.py -v
```

## File Structure

```
barb/backtest/
  __init__.py         — exports Strategy, run_backtest
  strategy.py         — Strategy dataclass, resolve_level()
  engine.py           — run_backtest(), _simulate(), _find_exit_in_minutes(), _check_exit_levels()
  metrics.py          — Trade, BacktestMetrics, BacktestResult, calculate_metrics()

assistant/tools/
  backtest.py         — BACKTEST_TOOL schema, run_backtest_tool(), _build_backtest_card(), _format_summary()

tests/
  test_backtest.py    — 76 tests (synthetic + real + minute resolution + metrics + trailing + breakeven + timeframe)
  test_data_blocks.py — 13 tests (query cards + backtest cards)
```

### Dependencies

```
barb/backtest/engine.py  ← barb/backtest/strategy.py (Strategy, resolve_level)
                         ← barb/backtest/metrics.py (Trade, BacktestResult, build_equity_curve, calculate_metrics)
                         ← barb/expressions (evaluate)
                         ← barb/functions (FUNCTIONS)
                         ← barb/ops (BarbError, resample)

assistant/tools/backtest.py ← barb/backtest/engine (run_backtest)
                            ← barb/backtest/strategy (Strategy)
                            ← barb/backtest/metrics (BacktestResult)
                            ← barb/ops (filter_session, filter_period)

assistant/chat.py ← assistant/tools/backtest (BACKTEST_TOOL, run_backtest_tool, _build_backtest_card)
```
