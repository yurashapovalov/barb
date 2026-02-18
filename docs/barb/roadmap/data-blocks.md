# Data Block Refactoring

Backend говорит фронту **что рисовать**. Каждый data block — `title` + массив типизированных `blocks`. Фронт итерирует по blocks, маппит `type` → компонент, передаёт data как props. Не угадывает, не парсит.

## Статус

- **Phase 1** (typed block format for queries) — DONE
- **Phase 2** (backtest blocks + frontend components) — DONE

Оба типа блоков (query и backtest) используют единый формат `{title, blocks: Block[]}`.

## Целевое состояние

```
message.data: DataCard[]

DataCard {
  title: string
  blocks: Block[]
}

Block = TableBlock | BarChartBlock | MetricsGridBlock | AreaChartBlock | HorizontalBarBlock
```

### Типы блоков

**table** — сортируемая таблица (tanstack)
```json
{
  "type": "table",
  "columns": ["date", "close", "chg"],
  "rows": [{"date": "2024-01-15", "close": 18450, "chg": -2.5}]
}
```

**bar-chart** — вертикальный bar chart (grouped query results)
```json
{
  "type": "bar-chart",
  "category_key": "dow",
  "value_key": "mean_r",
  "rows": [{"dow": "Mon", "mean_r": 150.3}]
}
```

**metrics-grid** — key-value сетка (backtest metrics)
```json
{
  "type": "metrics-grid",
  "items": [
    {"label": "Trades", "value": "71"},
    {"label": "Win Rate", "value": "53.5%"},
    {"label": "Total P&L", "value": "+1,798", "color": "green"}
  ]
}
```

**area-chart** — line + area overlay (equity curve + drawdown)
```json
{
  "type": "area-chart",
  "series": [
    {"key": "equity", "style": "line"},
    {"key": "drawdown", "style": "area", "color": "red"}
  ],
  "data": [
    {"date": "2024-01-15", "equity": 52.5, "drawdown": 0}
  ]
}
```

**horizontal-bar** — горизонтальные бары (exits breakdown)
```json
{
  "type": "horizontal-bar",
  "items": [
    {"label": "Stop", "value": -4468.3, "detail": "37 trades (W:0 L:37)"},
    {"label": "Take Profit", "value": 1789.0, "detail": "67 trades (W:42 L:25)"}
  ]
}
```

## Примеры

### Query: простой фильтр → 1 block

```json
{
  "title": "Падения >2.5%",
  "blocks": [
    {
      "type": "table",
      "columns": ["date", "close", "изменение"],
      "rows": [{"date": "2024-05-22", "close": 4.8485, "изменение": -5.04}]
    }
  ]
}
```

### Query: grouped с chart → 2 blocks

```json
{
  "title": "Range by day",
  "blocks": [
    {
      "type": "bar-chart",
      "category_key": "dow",
      "value_key": "mean_r",
      "rows": [{"dow": "Mon", "mean_r": 150.3}, {"dow": "Tue", "mean_r": 142.1}]
    },
    {
      "type": "table",
      "columns": ["dow", "mean_r"],
      "rows": [{"dow": "Mon", "mean_r": 150.3}, {"dow": "Tue", "mean_r": 142.1}]
    }
  ]
}
```

### Backtest → 4 blocks

```json
{
  "title": "RSI Mean Reversion",
  "blocks": [
    {
      "type": "metrics-grid",
      "items": [
        {"label": "Trades", "value": "71"},
        {"label": "Win Rate", "value": "53.5%"},
        {"label": "PF", "value": "1.38"},
        {"label": "Total P&L", "value": "+1,798", "color": "green"},
        {"label": "Avg Win", "value": "+173.3"},
        {"label": "Avg Loss", "value": "-145.0"},
        {"label": "Max DD", "value": "1,710"},
        {"label": "Recovery", "value": "1.05"}
      ]
    },
    {
      "type": "area-chart",
      "series": [
        {"key": "equity", "style": "line"},
        {"key": "drawdown", "style": "area", "color": "red"}
      ],
      "data": [
        {"date": "2024-01-15", "equity": 52.5, "drawdown": 0},
        {"date": "2024-01-22", "equity": 17.8, "drawdown": -34.7}
      ]
    },
    {
      "type": "horizontal-bar",
      "items": [
        {"label": "Stop", "value": -4468.3, "detail": "37 trades (W:0 L:37)"},
        {"label": "Take Profit", "value": 1789.0, "detail": "67 trades (W:42 L:25)"},
        {"label": "Timeout", "value": 910.5, "detail": "25 trades (W:17 L:8)"}
      ]
    },
    {
      "type": "table",
      "columns": ["entry_date", "exit_date", "entry_price", "exit_price", "pnl", "exit_reason", "bars_held"],
      "rows": [
        {"entry_date": "2025-04-09", "exit_date": "2025-04-09", "pnl": 507.9, "exit_reason": "take_profit", "bars_held": 0}
      ]
    }
  ]
}
```

## Реализация: Phase 1 — Query refactoring

Переводим существующие query data blocks на новый формат. Функциональность не меняется — те же таблицы и bar charts, просто формат чище.

### Backend

**`assistant/chat.py` → `_exec_query()`**

Было:
```python
block = {
    "query": query,
    "result": ui_data,
    "rows": len(ui_data),
    "columns": columns,
    "session": session,
    "timeframe": timeframe,
    "source_rows": source_rows,
    "source_row_count": source_row_count,
    "title": title,
    "chart": result.get("chart"),
}
```

Стало:
```python
blocks = []

chart = result.get("chart")
if chart:
    blocks.append({
        "type": "bar-chart",
        "category_key": chart["category"],
        "value_key": chart["value"],
        "rows": ui_data,
    })

blocks.append({
    "type": "table",
    "columns": columns,
    "rows": ui_data,
})

card = {"title": title, "blocks": blocks}
```

`run_query()` в `tools/__init__.py` не меняется — он возвращает model_response + raw data. Сборка card — в `_exec_query()`.

### Frontend

**`front/src/types/index.ts`**

```typescript
interface TableBlock {
  type: "table";
  columns: string[];
  rows: Record<string, unknown>[];
}

interface BarChartBlock {
  type: "bar-chart";
  category_key: string;
  value_key: string;
  rows: Record<string, unknown>[];
}

type Block = TableBlock | BarChartBlock;

interface DataCard {
  title: string;
  blocks: Block[];
  status?: "loading" | "success" | "error";
  error?: string;
}
```

**`front/src/components/ai/data-card.tsx`**

Упрощение: `formatLabel(data)` → `data.title ?? "Query result"`. Иконка — `TableIcon` (query), `ActivityIcon` (backtest, Phase 2).

**`front/src/components/panels/data-panel.tsx`**

```tsx
{data.blocks.map((block, i) => {
  switch (block.type) {
    case "bar-chart":
      return <BarChart key={i} data={block.rows} categoryKey={block.category_key} valueKey={block.value_key} />;
    case "table":
      return <DataTable key={i} columns={block.columns} rows={block.rows} />;
  }
})}
```

Существующие компоненты `BarChart` и таблица уже есть — меняется только как им передаются props.

**`front/src/hooks/use-chat.ts`**

Loading block:
```typescript
const loadingCard: DataCard = {
  title: "Loading...",
  blocks: [],
  status: "loading",
};
```

### Файлы

```
assistant/chat.py                              — _exec_query() новый формат (~15 строк)
front/src/types/index.ts                       — DataCard + Block types (~20 строк)
front/src/components/ai/data-card.tsx           — упрощённый label (~5 строк)
front/src/components/panels/data-panel.tsx      — block routing (~20 строк)
front/src/hooks/use-chat.ts                    — loading block format (~5 строк)
```

### Верификация

1. Query без chart → панель показывает таблицу (как раньше)
2. Query с grouped result → панель показывает bar chart + таблицу (как раньше)
3. Loading state → карточка с "Loading..."
4. Error state → карточка с ошибкой
5. Все e2e сценарии проходят

## Phase 2 — Backtest blocks

Бэктест возвращает `{type: "backtest", metrics, trades, equity_curve}` — старый плоский формат. Frontend его не понимает (isDataBlockEvent проверяет `title` + `blocks`). Нужно конвертировать в типизированные блоки.

### Что есть сейчас

`run_backtest_tool()` возвращает:
```python
{
    "model_response": "Backtest: 71 trades | Win Rate 53.5% | ...",
    "backtest": {
        "type": "backtest",
        "title": "RSI < 30 Лонг",
        "strategy": {...},
        "metrics": {
            "total_trades": 71, "win_rate": 53.5, "profit_factor": 1.38,
            "total_pnl": 1798.4, "max_drawdown": 1709.6, "avg_win": 173.2,
            "avg_loss": -145.0, "recovery_factor": 1.05, ...
        },
        "trades": [
            {"entry_date": "2008-01-18", "exit_date": "2008-01-21",
             "entry_price": 1870.5, "exit_price": 1833.09,
             "direction": "long", "pnl": -37.41, "exit_reason": "stop", "bars_held": 2}
        ],
        "equity_curve": [float, float, ...]  # без дат
    }
}
```

`_exec_backtest()` в `chat.py` передаёт `backtest` dict напрямую как data_block. Frontend отбрасывает — нет `blocks`.

### Целевое состояние

`_build_backtest_card()` конвертирует в `{title, blocks}`:

```json
{
  "title": "RSI < 30 Лонг · 71 trades",
  "blocks": [
    {
      "type": "metrics-grid",
      "items": [
        {"label": "Trades", "value": "71"},
        {"label": "Win Rate", "value": "53.5%"},
        {"label": "PF", "value": "1.38"},
        {"label": "Total P&L", "value": "+1,798", "color": "green"},
        {"label": "Avg Win", "value": "+173.3"},
        {"label": "Avg Loss", "value": "-145.0"},
        {"label": "Max DD", "value": "1,710"},
        {"label": "Recovery", "value": "1.05"}
      ]
    },
    {
      "type": "area-chart",
      "x_key": "date",
      "series": [
        {"key": "equity", "label": "Equity", "style": "line"},
        {"key": "drawdown", "label": "Drawdown", "style": "area", "color": "red"}
      ],
      "data": [
        {"date": "2008-01-21", "equity": -37.41, "drawdown": -37.41},
        {"date": "2008-02-05", "equity": 120.5, "drawdown": 0}
      ]
    },
    {
      "type": "horizontal-bar",
      "items": [
        {"label": "Stop", "value": -4468.3, "detail": "37 trades (W:0 L:37)"},
        {"label": "Take Profit", "value": 6106.2, "detail": "33 trades (W:33 L:0)"},
        {"label": "Timeout", "value": 160.5, "detail": "1 trade (W:1 L:0)"}
      ]
    },
    {
      "type": "table",
      "columns": ["entry_date", "exit_date", "direction", "entry_price", "exit_price", "pnl", "exit_reason", "bars_held"],
      "rows": [...]
    }
  ]
}
```

4 блока → 4 визуальных секции в панели.

### Новые типы блоков

**metrics-grid** — сетка key-value пар
```typescript
interface MetricsGridBlock {
  type: "metrics-grid";
  items: { label: string; value: string; color?: "green" | "red" }[];
}
```

Рендер: CSS grid 4 колонки. Value крупно, label мелко под ним. `color` для P&L (зелёный/красный).

**area-chart** — line + area overlay (equity curve + drawdown)
```typescript
interface AreaChartBlock {
  type: "area-chart";
  x_key: string;
  series: { key: string; label: string; style: "line" | "area"; color?: string }[];
  data: Record<string, unknown>[];
}
```

Рендер: Recharts `ComposedChart` с `Line` (equity) и `Area` (drawdown, красная зона). Данные приходят с бэка — фронт не считает drawdown.

**horizontal-bar** — горизонтальные бары (exits breakdown)
```typescript
interface HorizontalBarBlock {
  type: "horizontal-bar";
  items: { label: string; value: number; detail?: string }[];
}
```

Рендер: div с процентной шириной, зелёный/красный по знаку value. Detail мелким текстом.

### Backend: `_build_backtest_card()`

Новая функция в `assistant/tools/backtest.py`. Принимает `BacktestResult` + `title`. Возвращает `{title, blocks}`.

```python
def _build_backtest_card(result: BacktestResult, title: str) -> dict:
    m = result.metrics
    trades = result.trades

    # 1. metrics-grid
    metrics_block = {
        "type": "metrics-grid",
        "items": [
            {"label": "Trades", "value": str(m.total_trades)},
            {"label": "Win Rate", "value": f"{m.win_rate:.1f}%"},
            {"label": "PF", "value": _fmt_pf(m.profit_factor)},
            {"label": "Total P&L", "value": _fmt_pnl(m.total_pnl), "color": _pnl_color(m.total_pnl)},
            {"label": "Avg Win", "value": f"{m.avg_win:+.1f}"},
            {"label": "Avg Loss", "value": f"{m.avg_loss:.1f}"},
            {"label": "Max DD", "value": f"{m.max_drawdown:,.0f}"},
            {"label": "Recovery", "value": _fmt_rf(m.recovery_factor)},
        ],
    }

    # 2. area-chart — equity + drawdown (computed here, not on frontend)
    equity = 0.0
    peak = 0.0
    chart_data = []
    for t in trades:
        equity += t.pnl
        peak = max(peak, equity)
        chart_data.append({
            "date": str(t.exit_date),
            "equity": round(equity, 2),
            "drawdown": round(equity - peak, 2),
        })

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
    for t in trades:
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

    hbar_block = {
        "type": "horizontal-bar",
        "items": exit_items,
    }

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
        for t in trades
    ]

    table_block = {
        "type": "table",
        "columns": ["entry_date", "exit_date", "direction", "entry_price", "exit_price", "pnl", "exit_reason", "bars_held"],
        "rows": trade_rows,
    }

    card_title = f"{title} · {m.total_trades} trades"
    return {"title": card_title, "blocks": [metrics_block, area_block, hbar_block, table_block]}
```

`_exec_backtest()` в `chat.py` вызывает `_build_backtest_card()` вместо передачи raw dict:

```python
def _exec_backtest(self, input_data, title):
    result = run_backtest_tool(input_data, self.df_minute, self.sessions)
    model_response = result.get("model_response", "")
    backtest_result = result.get("backtest_result")  # BacktestResult object
    if not backtest_result:
        return model_response, None
    card = _build_backtest_card(backtest_result, title)
    return model_response, card
```

**Важно**: `run_backtest_tool` сейчас возвращает сериализованный dict. Нужно чтобы он также возвращал `BacktestResult` объект (для `_build_backtest_card`), или строить card прямо в `run_backtest_tool`.

Проще: `_build_backtest_card` принимает `result: BacktestResult, title: str` и живёт в `assistant/tools/backtest.py`. `run_backtest_tool` возвращает `BacktestResult` + `model_response`. `_exec_backtest` в `chat.py` вызывает `_build_backtest_card`.

### Frontend: новые компоненты

**`front/src/types/index.ts`** — добавить 3 типа в `Block` union:
```typescript
interface MetricsGridBlock {
  type: "metrics-grid";
  items: { label: string; value: string; color?: "green" | "red" }[];
}

interface AreaChartBlock {
  type: "area-chart";
  x_key: string;
  series: { key: string; label: string; style: "line" | "area"; color?: string }[];
  data: Record<string, unknown>[];
}

interface HorizontalBarBlock {
  type: "horizontal-bar";
  items: { label: string; value: number; detail?: string }[];
}

type Block = TableBlock | BarChartBlock | MetricsGridBlock | AreaChartBlock | HorizontalBarBlock;
```

**`front/src/components/charts/metrics-grid.tsx`** — новый
```
CSS grid, 4 колонки. Каждый item: value крупно, label мелко. color → text-green-500 / text-red-500.
```

**`front/src/components/charts/area-chart.tsx`** — новый
```
Recharts ComposedChart. Line для equity, Area для drawdown.
Responsive. Tooltip с датой и значениями.
```

**`front/src/components/charts/horizontal-bar.tsx`** — новый
```
div с процентной шириной = |value| / max(|values|) * 100%.
Зелёный (value > 0) / красный (value < 0). Label слева, value справа, detail мелко.
```

**`front/src/components/panels/data-panel.tsx`** — добавить case в switch:
```tsx
case "metrics-grid":
  return <MetricsGrid key={i} items={block.items} />;
case "area-chart":
  return <AreaChart key={i} ... />;
case "horizontal-bar":
  return <HorizontalBar key={i} items={block.items} />;
```

### Шаги реализации

```
1. Backend: _build_backtest_card() + тесты              — assistant/tools/backtest.py
2. Backend: run_backtest_tool возвращает BacktestResult  — assistant/tools/backtest.py
3. Backend: _exec_backtest вызывает _build_backtest_card — assistant/chat.py
4. Frontend types: 3 новых блока в Block union           — front/src/types/index.ts
5. Frontend: MetricsGrid компонент                       — front/src/components/charts/metrics-grid.tsx
6. Frontend: AreaChart компонент (recharts)               — front/src/components/charts/area-chart.tsx
7. Frontend: HorizontalBar компонент                     — front/src/components/charts/horizontal-bar.tsx
8. Frontend: DataPanel switch cases                      — front/src/components/panels/data-panel.tsx
9. E2E: прогнать backtest сценарий, сохранить JSON
10. Docs: обновить data-blocks.md Phase 2 как ✓
```

### Верификация

1. `pytest tests/test_data_blocks.py -v` — тесты `_build_backtest_card()`
2. `pytest tests/test_backtest.py -v` — существующие тесты не ломаются
3. `npm run build` — TypeScript компилируется
4. `npx vitest run` — frontend тесты проходят
5. E2E сценарий 11 (RSI backtest) — data block в новом формате с 4 блоками
6. Dev server: клик на backtest карточку → панель с метриками, equity curve, exits, trades
