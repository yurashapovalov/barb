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

1. **Stop loss** — low (long) или high (short) пересекает стоп-цену
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
    exit_reason: str        # "stop" | "take_profit" | "target" | "timeout" | "end"
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
- [x] `assistant/tools/backtest.py` — 5-line model_response (yearly, exit types, concentration)
- [x] `assistant/prompt/system.py` — rule #9 rewrite (analyze quality, not repeat numbers)
- [x] `barb/backtest/strategy.py` + `engine.py` — commission field
- [x] 54 теста total

---

### Phase 5: Frontend Backtest Panel

#### Контекст

Backend бэктеста готов — 54 теста, 5-строчная аналитика, Claude даёт качественные рекомендации. Но пользователь **ничего не видит** — фронтенд рендерит backtest data_block как generic DataCard (иконка таблицы, пустое содержимое). Equity curve, метрики, trades — всё есть в данных, но UI не показывает.

Текущий фронтенд не знает о типе `backtest`:
- `DataBlock` интерфейс не имеет поля `type`
- `data-card.tsx` рендерит все блоки одинаково
- `data-panel.tsx` пытается показать как таблицу — показывает мусор

#### Подход

Существующий паттерн: DataCard в чате → клик → DataPanel в правой панели. Для бэктеста тот же паттерн: карточка в чате (заголовок с title бэктеста) → клик → правая панель с бэктест-контентом вместо таблицы данных.

Минимум изменений в chat flow. Вся работа — в панели.

#### Layout панели (сверху вниз, по важности для трейдера)

##### 1. Metrics Summary — компактная сетка 4×2

```
┌──────────────────────────────────────────────┐
│  RSI < 30 Long                               │
├──────────┬──────────┬──────────┬─────────────┤
│ 71       │ 53.5%    │ 1.38     │ +1,798 pts  │
│ Trades   │ Win Rate │ PF       │ Total P&L   │
├──────────┼──────────┼──────────┼─────────────┤
│ +173.3   │ -145.0   │ 1,710    │ 1.05        │
│ Avg Win  │ Avg Loss │ Max DD   │ Recovery    │
└──────────┴──────────┴──────────┴─────────────┘
```

8 ключевых метрик. Достаточно чтобы за секунду понять — стратегия рабочая или нет. Total P&L зелёный если плюс, красный если минус.

##### 2. Equity Curve + Drawdown overlay

```
┌──────────────────────────────────────────────┐
│  ╱╲    ╱╲                                    │
│ ╱  ╲  ╱  ╲      ╱╲  ╱╲    ╱╲               │  equity (line)
│╱    ╲╱    ╲    ╱  ╲╱  ╲  ╱  ╲    ╱         │
│           ╲  ╱         ╲╱    ╲  ╱           │
│            ╲╱                  ╲╱            │
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  drawdown (area, red, under)
└──────────────────────────────────────────────┘
```

Recharts (уже в проекте). Line chart для equity, Area chart для drawdown (красная полупрозрачная область). Drawdown считается на фронте из equity_curve: `drawdown[i] = equity[i] - max(equity[0..i])`.

##### 3. Exits Breakdown — P&L по типу выхода

```
┌──────────────────────────────────────────────┐
│ Stop        32 trades    -4,759 pts   ██████ │
│ Take Profit 33 trades    +6,106 pts   ██████ │
│ Timeout      6 trades      +451 pts   ██     │
└──────────────────────────────────────────────┘
```

Горизонтальные бары. Зелёный для плюса, красный для минуса. Считается на фронте из trades (group by exit_reason, sum pnl).

##### 4. Trades Table — tanstack/react-table (уже в проекте)

```
┌─────────────┬─────────────┬─────────┬────────┬──────┐
│ Entry       │ Exit        │ P&L     │ Reason │ Bars │
├─────────────┼─────────────┼─────────┼────────┼──────┤
│ 2025-04-09  │ 2025-04-09  │ +507.9  │ TP     │  0   │
│ 2025-04-07  │ 2025-04-07  │ +504.3  │ TP     │  0   │
│ 2025-03-11  │ 2025-03-17  │ +583.0  │ TP     │  5   │
└─────────────┴─────────────┴─────────┴────────┴──────┘
```

P&L зелёный/красный. Сортировка по любой колонке. По умолчанию по дате desc (новые сверху).

#### Изменения

##### 1. `front/src/types/index.ts` — Тип BacktestBlock

```typescript
export interface BacktestBlock {
  type: "backtest";
  title: string;
  strategy: {
    entry: string;
    direction: "long" | "short";
    exit_target?: string | null;
    stop_loss?: number | string | null;
    take_profit?: number | string | null;
    exit_bars?: number | null;
    slippage: number;
    commission: number;
  };
  metrics: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    profit_factor: number;
    avg_win: number;
    avg_loss: number;
    max_drawdown: number;
    total_pnl: number;
    expectancy: number;
    avg_bars_held: number;
    max_consecutive_wins: number;
    max_consecutive_losses: number;
    recovery_factor: number;
    gross_profit: number;
    gross_loss: number;
  };
  trades: {
    entry_date: string;
    exit_date: string;
    entry_price: number;
    exit_price: number;
    direction: string;
    pnl: number;
    exit_reason: string;
    bars_held: number;
  }[];
  equity_curve: number[];
}
```

Дискриминация: `"type" in block && block.type === "backtest"` → BacktestBlock, иначе DataBlock.

##### 2. `front/src/components/ai/data-card.tsx` — Лейбл для бэктеста

Минимальное изменение: если блок — backtest, показать title из бэктеста вместо generic label. Та же карточка, другой текст. Клик → открывает панель (как сейчас).

##### 3. `front/src/components/panels/data-panel.tsx` — Маршрутизация

Если блок — backtest → рендерить `BacktestPanel` вместо таблицы данных.

##### 4. `front/src/components/backtest/backtest-panel.tsx` — Панель

4 секции сверху вниз: metrics grid, equity+drawdown chart, exits breakdown, trades table. Каждая секция — отдельный компонент.

##### 5. `front/src/components/backtest/equity-chart.tsx` — Recharts

ComposedChart: Line (equity) + Area (drawdown). Drawdown считается из equity_curve.

##### 6. `front/src/components/backtest/exits-breakdown.tsx` — Бары по exit type

Группируем trades по exit_reason, считаем count и sum pnl. Горизонтальные бары с цветом.

##### 7. `front/src/components/backtest/trades-table.tsx` — Tanstack table

Переиспользуем паттерн существующей таблицы. Сортировка, цвета P&L.

#### Файлы

```
front/src/types/index.ts                           — BacktestBlock тип (~30 строк)
front/src/components/ai/data-card.tsx               — backtest label (~5 строк)
front/src/components/panels/data-panel.tsx           — маршрутизация (~10 строк)
front/src/components/backtest/backtest-panel.tsx     — layout 4 секций (~40 строк)
front/src/components/backtest/metrics-grid.tsx       — 4×2 сетка метрик (~50 строк)
front/src/components/backtest/equity-chart.tsx       — recharts line+area (~60 строк)
front/src/components/backtest/exits-breakdown.tsx    — горизонтальные бары (~50 строк)
front/src/components/backtest/trades-table.tsx       — tanstack table (~80 строк)
```

~325 строк нового кода, 3 файла модифицированы, 5 новых файлов.

#### НЕ в Phase 5

- **Monthly returns heatmap** — красиво, позже.
- **Strategy comparison side-by-side** — нужна поддержка нескольких блоков.
- **Downloadable CSV** — экспорт trades.
- **By year breakdown в панели** — модель уже пишет это в чате, дублировать не нужно.
- **MAE/MFE scatter plot** — нет данных в Trade dataclass.
- **Parameter sensitivity** — другая фича целиком.

#### Верификация

1. `cd front && npm run dev` — запустить dev server
2. Бэктест запрос → карточка в чате с title бэктеста (не generic "Table")
3. Клик на карточку → правая панель с 4 секциями
4. Metrics grid: 8 метрик, Total P&L зелёный/красный
5. Equity curve: линия + красный drawdown overlay
6. Exits breakdown: бары по exit type с P&L
7. Trades table: сортировка по дате desc, P&L с цветом
8. 0 trades → сообщение "No trades" вместо пустых секций

---

### Phase 6: Advanced Metrics + Validation

- MAE/MFE per trade — track running min/max during trade in engine
- Sharpe/Sortino/Calmar — percentage returns, annualization
- Train/Test Split — in-sample / out-of-sample comparison
- Walk-Forward analysis — rolling window validation
- Monthly heatmap, strategy comparison

### Phase 7: Realistic Fills

- `fill_mode` — market / limit / stop
- `slippage_atr` — dynamic slippage based on ATR
- Trailing stop
- Position sizing