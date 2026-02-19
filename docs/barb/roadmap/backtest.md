# Backtest Module

Тестирование торговых стратегий на исторических данных без кода. Пользователь описывает стратегию на естественном языке — система симулирует сделки и возвращает метрики.

## User Experience

```
User: "Протестируй стратегию: лонг когда RSI ниже 30, стоп 2%, тейк 3%, максимум 5 дней. 2024."

Barb: Тестирую стратегию на RSI oversold...

[Strategy Results Card]
Trades: 93
Win Rate: 47.3%
Profit Factor: 1.31
Avg Win: 42.5 pts
Avg Loss: -20.0 pts
Max Drawdown: -156 pts
Total P&L: +847 pts

[Equity Curve — area chart]

[Trades Table — expandable]
```

## Архитектура

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

Принцип тот же, что и в Query Engine: `barb/backtest/` — чистый Python без зависимости от LLM. Можно использовать из CLI, тестов, ноутбуков. `assistant/tools/backtest.py` — тонкая обёртка для Claude.

## Strategy Definition

```python
@dataclass
class Strategy:
    entry: str                  # Expression: "gap > 50"
    direction: str              # "long" | "short"
    exit_target: str | None     # Expression evaluated ONCE at entry → fixed price. E.g. "prev(close)" for gap fill
    stop_loss: float | None     # Points (or percentage if ends with %)
    take_profit: float | None   # Points (or percentage if ends with %)
    trailing_stop: float | None # Trail distance in points or "2%". Stop follows price.
    exit_bars: int | None       # Max bars in trade or None
    slippage: float             # Points per side, default 0
```

### Stop/Target: пункты vs проценты

У нас 10K инструментов — акция за $20 и NQ за 20000. Стоп в пунктах бессмысленно сравнивать. Поддерживаем оба формата:

- **Число** → пункты: `stop_loss: 20` = 20 пунктов от входа
- **Строка с %** → проценты: `stop_loss: "1%"` = 1% от цены входа

Claude определяет формат из контекста. Если пользователь говорит "стоп 20 пунктов" → число. "Стоп 1%" → строка.

```python
def resolve_stop(stop_value, entry_price) -> float:
    """Convert stop to absolute points."""
    if isinstance(stop_value, str) and stop_value.endswith("%"):
        pct = float(stop_value.rstrip("%"))
        return entry_price * pct / 100
    return float(stop_value)
```

## Tool Schema

```python
BACKTEST_TOOL = {
    "name": "run_backtest",
    "description": """Test a trading strategy on historical data.

Returns simulated trades with entry/exit prices and performance metrics.
Uses the same expressions as run_query for entry/exit conditions.

Stop/target accept points (number) or percentage (string with %).
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
                        "enum": ["long", "short"]
                    },
                    "exit_target": {
                        "type": "string",
                        "description": "Expression evaluated ONCE at entry to get target price. E.g. 'prev(close)' for gap fill"
                    },
                    "stop_loss": {
                        "description": "Stop loss. Number = points, string with % = percentage. E.g. 20 or '1%'"
                    },
                    "take_profit": {
                        "description": "Take profit. Number = points, string with % = percentage. E.g. 50 or '2%'"
                    },
                    "exit_bars": {
                        "type": "integer",
                        "description": "Force exit after N bars if no stop/target hit"
                    },
                    "slippage": {
                        "type": "number",
                        "description": "Slippage in points per side, default 0"
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

## Engine

### Pipeline

Движок переиспользует инфраструктуру Query Engine — сессии, периоды, expressions:

```
Входные данные (минутный DataFrame)
    ↓
1. session filter     — переиспользует barb/interpreter session logic
2. period filter      — переиспользует barb/interpreter period logic
3. resample to daily  — OHLCV дневные бары
4. evaluate entry     — expressions.py вычисляет условие на каждом баре
5. simulate trades    — для каждого сигнала: вход → выход → P&L
6. calculate metrics  — агрегатные метрики + equity curve
    ↓
BacktestResult
```

```python
def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    sessions: dict,
    session: str = "RTH",
    period: str | None = None,
) -> BacktestResult:
```

### Entry Logic

- Условие входа вычисляется на дневных барах (все OHLCV бара доступны)
- **Вход на open СЛЕДУЮЩЕГО бара** после сигнала — стандарт в бэктестинге. Условия часто используют `close`, который известен только по завершении бара
- Одна сделка одновременно (нет overlapping positions). Сигналы во время открытой позиции пропускаются

```
Bar N: entry condition = True (evaluated with full OHLCV of bar N)
Bar N+1: entry at open (adjusted for slippage)
```

Примечание: для gap-стратегий (условие на `open`) вход на следующем баре означает "шорт день после гэпа", а не "шорт в момент гэпа". Это осознанное решение — единый timing для всех стратегий. Intraday entry (same-bar) — потенциально v2.

### Exit Logic (по приоритету)

1. **Stop loss / Trailing stop** — low (long) или high (short) пересекает стоп-цену. При trailing — стоп двигается за ценой
2. **Take profit** — high (long) или low (short) пересекает тейк-цену
3. **Exit target** — цена достигает target price (вычисляется ОДИН РАЗ при входе из `exit_target` expression)
4. **Exit bars** — максимальная длительность сделки
5. **End of data** — принудительное закрытие на последнем баре

### Stop/Target Resolution на дневных барах

Для симуляции стопа/тейка внутри дневного бара:
- Проверяем, мог ли стоп ИЛИ тейк сработать (по high/low)
- Если оба могли сработать — считаем что стоп сработал первым (conservative assumption)
- Это пессимистичная оценка — реальные результаты могут быть лучше

У нас есть минутные данные — можно точно определить что сработало первым. Но это x100 медленнее (проход по минутным барам вместо дневных). V1 использует дневные бары с conservative assumption. Минутная симуляция — потенциально v2 для точных результатов.

### Slippage

Простая модель: фиксированное проскальзывание в пунктах на каждую сторону сделки.

```python
# Long entry: buy higher
actual_entry = entry_price + slippage
# Long exit: sell lower
actual_exit = exit_price - slippage

# Short entry: sell lower
actual_entry = entry_price - slippage
# Short exit: buy higher
actual_exit = exit_price + slippage
```

Default = 0. Claude может предложить slippage если пользователь не указал, но не навязывает.

## Результат

### Data Structures

```python
@dataclass
class Trade:
    entry_date: date
    entry_price: float
    exit_date: date
    exit_price: float
    direction: str          # "long" | "short"
    pnl: float              # points (after slippage)
    exit_reason: str        # "stop" | "trailing_stop" | "take_profit" | "target" | "timeout" | "end"
    bars_held: int          # сколько баров в позиции
```

```python
@dataclass
class BacktestMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float             # winning / total
    profit_factor: float        # gross_profit / abs(gross_loss), inf if no losses
    avg_win: float              # points
    avg_loss: float             # points
    max_drawdown: float         # points (peak to trough of equity curve)
    total_pnl: float            # points
    expectancy: float           # avg pnl per trade
    avg_bars_held: float        # среднее время в позиции
    max_consecutive_wins: int
    max_consecutive_losses: int
```

```python
@dataclass
class BacktestResult:
    trades: list[Trade]
    metrics: BacktestMetrics
    equity_curve: list[float]   # cumulative P&L after each trade
```

### Формат для модели vs UI

Тот же принцип что и в Query Engine — модель получает компактный summary, UI получает полные данные:

**Модель получает:**
```
Backtest: 93 trades, Win Rate 47.3%, PF 1.31, Total +847 pts, Max DD -156 pts
```

**UI получает (через SSE data_block):**
```json
{
  "type": "backtest",
  "metrics": { ... },
  "trades": [ ... ],
  "equity_curve": [ ... ]
}
```

## Frontend Display

### Strategy Results Card

Ключевые метрики одним взглядом:

```
┌────────────────────────────────────────────┐
│  Gap Short Strategy (2024)                 │
├────────────────────────────────────────────┤
│  Trades    93      Win Rate    47.3%       │
│  PF        1.31    Expectancy  +9.1 pts    │
│  Total P&L +847    Max DD      -156 pts    │
├────────────────────────────────────────────┤
│  [Equity Curve — area chart]               │
│       ╭────────                            │
│    ╭──╯                                    │
│  ──╯                                       │
├────────────────────────────────────────────┤
│  ▼ Show 93 trades                          │
└────────────────────────────────────────────┘
```

### Equity Curve

Area chart (Shadcn/Recharts). Строится из `equity_curve` — cumulative P&L. Это буквально `cumsum(trade.pnl)`. Визуально — самый мощный элемент результата.

### Trades Table (expandable)

| Date | Dir | Entry | Exit | P&L | Reason | Bars |
|------|-----|-------|------|-----|--------|------|
| 2024-01-15 | Short | 18450 | 18400 | +50 | target | 1 |
| 2024-01-22 | Short | 18200 | 18220 | -20 | stop | 1 |

## Примеры

### Mean Reversion After Gap Up

```
"После гэпа вверх >50, шорт на следующий день, тейк на уровне закрытия гэп-дня, стоп 20. 2024."

→ run_backtest({
    strategy: {
      entry: "open - prev(close) > 50",
      direction: "short",
      exit_target: "close",
      stop_loss: 20
    },
    period: "2024",
    session: "RTH",
    title: "Short After Gap Up >50pts"
  })
```

Логика: bar N — гэп вверх >50. Bar N+1 — вход short на open. Target = bar N's close (вычисляется при входе из `exit_target: "close"`, т.е. close signal bar'а). Стоп 20 пунктов.

### Reversal After Big Down Day

```
"Лонг после дней с падением >2.5%, тейк 1%, стоп 0.5%. 2024."

→ run_backtest({
    strategy: {
      entry: "(prev(close) - prev(open)) / prev(open) < -0.025",
      direction: "long",
      take_profit: "1%",
      stop_loss: "0.5%"
    },
    period: "2024",
    session: "RTH",
    title: "Long After Big Drop"
  })
```

### Friday Reversal

```
"Шорт в пятницу если неделя выросла >3%, держать до конца дня."

→ run_backtest({
    strategy: {
      entry: "dayofweek() == 4 and (close - prev(close, 5)) / prev(close, 5) > 0.03",
      direction: "short",
      exit_bars: 1
    },
    period: "2024",
    session: "RTH",
    title: "Friday Reversal Short"
  })
```

### Mean Reversion с процентным стопом

```
"Лонг когда RSI ниже 30, стоп 2%, тейк 3%, максимум 5 дней."

→ run_backtest({
    strategy: {
      entry: "rsi(close, 14) < 30",
      direction: "long",
      stop_loss: "2%",
      take_profit: "3%",
      exit_bars: 5
    },
    period: "2023:2024",
    session: "RTH",
    title: "RSI Mean Reversion"
  })
```

## SSE Events

Бэктест интегрируется в существующий SSE поток:

```
event: tool_start
data: {"tool_name": "run_backtest", "input": {...}}

event: data_block
data: {"type": "backtest", "metrics": {...}, "trades": [...], "equity_curve": [...]}

event: tool_end
data: {"tool_name": "run_backtest", "duration_ms": 450, "error": null}
```

Frontend рендерит `data_block` с `type: "backtest"` как Strategy Results Card вместо обычной таблицы.

## Design Decisions

| Вопрос | Решение | Почему |
|--------|---------|--------|
| Entry timing | Open следующего бара | Единый timing для всех стратегий. Условия часто используют close. Same-bar entry — v2 |
| Пункты vs проценты | Оба: число = пункты, "N%" = проценты | 10K инструментов с разными ценами — проценты универсальнее |
| Multiple timeframes | Только один (daily) | Усложнение x5. Минутная симуляция стопов — v2 |
| Equity curve | v1 | 3 строки кода (`cumsum`), но визуально самый мощный элемент |
| Slippage | Опционально, default 0 | Без slippage — нереалистично хорошие результаты, но навязывать не стоит |
| Conservative assumption | Стоп первый при неопределённости | Честно. Пользователь должен доверять результатам |
| Overlapping trades | Нет, одна сделка одновременно | Простота. Позиционный сайзинг — v2 |

## Implementation Plan

### Phase 1: Core Engine ✓
- [x] `barb/backtest/strategy.py` — Strategy dataclass + resolve_level
- [x] `barb/backtest/engine.py` — Backtest loop (entry next bar, exit priority chain)
- [x] `barb/backtest/metrics.py` — Trade, BacktestMetrics, BacktestResult + calculate_metrics + build_equity_curve
- [x] `tests/test_backtest.py` — 28 тестов (синтетические + реальные NQ данные)

### Phase 2: Tool Integration ✓
- [x] `assistant/tools/backtest.py` — BACKTEST_TOOL schema + run_backtest_tool wrapper + date serialization
- [x] `assistant/chat.py` — dispatch refactor (_exec_query + _exec_backtest), two tools
- [x] `assistant/prompt/system.py` — behavior rule #9 (strategy testing)
- [x] SSE event: data_block с type "backtest"
- [x] E2E тесты: сценарий RSI + multi-turn hammer strategy

### Phase 3: Minute-Level Exit Resolution ✓
- [x] `barb/backtest/engine.py` — `_find_exit_in_minutes()` walks minute bars chronologically
- [x] Fallback to daily bar conservative assumption when minute data unavailable
- [x] Integration test: same data, different outcome with/without minute bars

### Phase 4: Metrics + AI Commentary + Commission ✓
- [x] `barb/backtest/metrics.py` — recovery_factor, gross_profit, gross_loss
- [x] `assistant/tools/backtest.py` — 5-line model_response (yearly, exit types W/L, concentration, best/worst, consec W/L)
- [x] `assistant/prompt/system.py` — rule #9 rewrite (analyze quality, not repeat numbers)
- [x] `barb/backtest/strategy.py` + `engine.py` — commission field
- [x] 64 тестов total (56 core + 8 trailing stop)

---

### Phase 5: Frontend — Data Panel + Backtest Content

#### Контекст

Backend бэктеста готов — 56 тестов, 5-строчная аналитика, Claude даёт качественные рекомендации. Но пользователь **ничего не видит** — фронтенд рендерит backtest data_block как generic DataCard (иконка таблицы, пустое содержимое).

Текущий фронтенд не знает о типе `backtest`:
- `DataBlock` интерфейс не имеет поля `type`
- `data-card.tsx` рендерит все блоки одинаково
- `data-panel.tsx` пытается показать как таблицу — показывает мусор

#### Подход

**Одна DataPanel — разный контент.** Панель — generic контейнер (header, scroll, close). Контент определяется типом данных. Каждый визуальный блок (таблица, chart, metrics grid) — отдельный переиспользуемый компонент. Query и backtest показываются в одной и той же панели, просто собираются разные блоки.

```
DataPanel (generic container)
  ├── PanelHeader + close button  — общий
  ├── title                        — общий
  └── content blocks               — зависят от типа данных
       │
       ├── QueryBlock (type === undefined):
       │     ├── BarChart (если есть chart hint)
       │     └── Table (source_rows)
       │
       └── BacktestBlock (type === "backtest"):
             ├── MetricsGrid (metrics → 4×2 key-value)
             ├── LineChart (equity_curve → line + drawdown area)
             ├── BarChart (by_exit → горизонтальные бары)
             └── Table (trades → tanstack)
```

Компоненты generic — не знают про backtest. `MetricsGrid` принимает массив `{label, value}`. `Table` принимает rows и columns. `BarChart` принимает data, categoryKey, valueKey. Те же компоненты, разные данные.

#### Backend: structured data для фронта

Бэкенд уже считает yearly/exit/concentration для model_response. Нужно добавить эти же данные как structured JSON в backtest response — фронт рендерит, не считает.

`assistant/tools/backtest.py` — добавить в backtest dict:

```python
"equity_curve": [{"date": "2024-01-15", "value": 52.5}, ...],
"by_year": [{"year": 2024, "pnl": 2555.0, "trades": 90}, ...],
"by_exit": [{"reason": "stop", "trades": 43, "pnl": -1800.5, "wins": 0, "losses": 43}, ...],
"concentration": {"top_n": 3, "pnl": 1850.0, "pct_of_total": 72.4},
```

Engine (`barb/backtest/`) не меняется. Всё в tool wrapper.

#### Layout панели (сверху вниз)

##### 1. Metrics Grid — 4×2

```
┌──────────┬──────────┬──────────┬─────────────┐
│ 71       │ 53.5%    │ 1.38     │ +1,798 pts  │
│ Trades   │ Win Rate │ PF       │ Total P&L   │
├──────────┼──────────┼──────────┼─────────────┤
│ +173.3   │ -145.0   │ 1,710    │ 1.05        │
│ Avg Win  │ Avg Loss │ Max DD   │ Recovery    │
└──────────┴──────────┴──────────┴─────────────┘
```

Generic компонент `MetricsGrid` — принимает `{label, value, color?}[]`. Backtest передаёт 8 метрик. Компонент не знает что это backtest.

##### 2. Equity Curve + Drawdown

Recharts ComposedChart: Line (equity) + Area (drawdown, красная). Drawdown = `equity[i] - max(equity[0..i])`, считается на фронте (3 строки, pure derived view). Данные приходят с бэка как `[{date, value}]`.

##### 3. Exits Breakdown

Горизонтальные бары по exit_reason. Данные приходят с бэка как `[{reason, trades, pnl, wins, losses}]`. Зелёный/красный по знаку pnl. Переиспользует `BarChart` или простой div с процентной шириной.

##### 4. Trades Table

Tanstack table — тот же компонент что для query, другие столбцы. P&L зелёный/красный. По умолчанию date desc.

#### Шаги реализации

##### 1. Backend: structured data
`assistant/tools/backtest.py` — добавить `equity_curve` с датами, `by_year`, `by_exit`, `concentration` в response dict. Тесты.

##### 2. Types
`front/src/types/index.ts` — `DataBlock` → discriminated union (`QueryBlock | BacktestBlock`). Дискриминация по полю `type`.

##### 3. DataCard
`front/src/components/ai/data-card.tsx` — иконка `ActivityIcon` для backtest, label из `title`.

##### 4. DataPanel content routing
`front/src/components/panels/data-panel.tsx` — `type === "backtest"` → backtest content blocks, иначе текущий query content.

##### 5. Generic components
- `MetricsGrid` — grid из `{label, value, color?}[]`
- `EquityChart` — recharts Line + Area (equity + drawdown)
- Exits breakdown — горизонтальные бары
- Trades table — те же tanstack columns, другие данные

#### НЕ в Phase 5

- Monthly returns heatmap
- Strategy comparison side-by-side
- Downloadable CSV
- By year breakdown в панели (Claude пишет в чате)
- MAE/MFE scatter plot
- Parameter sensitivity

---

### Phase 6: Exit Management

Вызвано реальными вопросами пользователей. Текущий движок: фиксированный стоп/тейк + timeout. Трейдерам нужно больше.

#### 6a. Breakeven ✱ маленькое изменение

После N баров, если сделка в прибыли → стоп перемещается на цену входа.

```
Вход long @ 100.0, SL @ 95.0, breakeven_bars = 20
Бар 1-19:  стоп = 95.0
Бар 20:    если в прибыли → стоп = 100.0
Бар 21+:   стоп = 100.0 (если активирован)
```

- `strategy.py`: `breakeven_bars: int | None = None`
- `engine.py` / `_simulate`: после N баров проверить `price > entry` (long), если да → `stop = entry + slippage`
- Позже: `breakeven_distance: float` — по расстоянию вместо баров

#### 6b. Trailing stop ✓

Стоп двигается за ценой. Нужен для трендовых стратегий — фиксированный тейк отсекает длинные движения.

```
Вход long @ 100, trail = 2
Цена: 101 → стоп 99, 103 → стоп 101, 105 → стоп 103, 102 → выход @ 103
```

- `strategy.py`: `trailing_stop: float | str | None` (пункты или "2%")
- `engine.py`: `best_price` побарово, `_pick_tighter_stop()` — trailing + fixed stop coexist
- На минутках: обновлять `best_price` каждую свечу, `exit_reason = "trailing_stop"`
- 8 тестов: basic long/short, percentage, with fixed stop, immediate loss, minute precision, with TP, distinct reason

#### 6c. Scale out ✱ большое, можно отложить

Закрытие частями: 50% на +1%, 50% на +2%.

- `strategy.py`: `scale_out: list[dict] | None` → `[{"at": "1%", "size": 50}]`
- `engine.py`: трекать `remaining_size`, partial P&L
- Можно аппроксимировать двумя отдельными бэктестами

Порядок: breakeven → trailing → scale out.

---

### Phase 7: Intraday Timeframe ✱ средний рефактор

Текущий движок всегда `resample(df, "daily")`. `hour()` и `minute()` = 0 на дневных барах. Нельзя тестировать стратегии с входом в конкретное время.

Реальный вопрос пользователя: "optimal time to enter if SL 50, target 100, breakeven 20 min after entry" → ассистент сделал 10 безуспешных попыток.

**Архитектурное решение:** `from`/timeframe — pipeline field, не Strategy field. Как session и period. Стратегия определяет ЧТО торговать (entry, exit), pipeline определяет на каких данных (session, period, timeframe). Так же устроено в TradingView, Backtrader, QuantConnect.

```python
# engine.py — одна строка вместо hardcode
def run_backtest(df, strategy, sessions, session=None, period=None, timeframe="daily"):
    bars = resample(df, timeframe)
```

```python
# tool schema — from рядом с session и period
"from": {"type": "string", "description": "Bar timeframe (default: daily)"}
```

**Сложности (не в архитектуре, а в simulation loop):**

- **Minute exit resolution:** сейчас `minute_by_date` ищет точный выход внутри дневного бара. Для часовых баров — нужно искать минутки внутри часа. Структуру нужно менять.
- **Производительность:** daily = ~4K баров, hourly = ~100K, minute = ~5M. Simulate loop x25-x1000 медленнее.
- **Session boundaries:** на часовых барах — CME halt 17:00-18:00, дырки в данных.
- **exit_bars семантика:** "5 баров" = 5 часов на 1h, 5 дней на daily. Документировать.

---

### Phase 8: Realistic Fills

- `fill_mode` — optimistic (current), realistic, pessimistic
- `slippage_atr` — adaptive slippage as fraction of ATR(14)
- `tp_must_exceed` — price must exceed, not just touch TP level
- Position sizing

См. `backtest-v3-fills.md` для деталей.

---

### Phase 9: Advanced Metrics + Validation

- MAE/MFE per trade — track running min/max during trade in engine (минутные данные уже есть)
- Sharpe/Sortino/Calmar — percentage returns, annualization
- Monte Carlo — рандомно перетасовать порядок сделок 1000x, distribution P&L/drawdown
- Train/Test Split — in-sample / out-of-sample comparison
- Walk-Forward analysis — rolling window validation
- Monthly heatmap, strategy comparison