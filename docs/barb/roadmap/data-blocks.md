# Data Block Refactoring

Backend говорит фронту **что рисовать**. Каждый data block — `title` + массив типизированных `blocks`. Фронт итерирует по blocks, маппит `type` → компонент, передаёт data как props. Не угадывает, не парсит.

## Текущее состояние

Data block — плоский dict с query-specific полями. Frontend угадывает что рисовать.

### Backend (`chat.py → _exec_query()`)

```python
block = {
    "query": query,
    "result": ui_data,           # rows для таблицы
    "rows": len(ui_data),
    "columns": columns,
    "session": session,
    "timeframe": timeframe,
    "source_rows": source_rows,
    "source_row_count": count,
    "title": title,
    "chart": {"category": "dow", "value": "mean_r"},  # or None
}
```

### Frontend (`data-panel.tsx`)

```
getChartInfo(data) → есть chart hint? → BarChart
normalizeResult(data.source_rows ?? data.result) → Table
```

Проблемы:
- Нет `type` — фронт угадывает по наличию полей
- `chart` hint — ad-hoc механизм (`{"category", "value"}`)
- Нельзя добавить новые визуализации без новых ad-hoc полей
- Backtest не влезает в этот формат

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

Добавляем новые типы блоков: `metrics-grid`, `area-chart`, `horizontal-bar`. Подробный план — в `docs/barb/roadmap/backtest.md`, Phase 5.
