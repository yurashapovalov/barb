# Charts & Visualizations

Графики дополняют таблицы. Некоторые паттерны проще увидеть на графике чем в числах.

## Компоненты

Два standalone chart компонента + три inline block view в `data-panel.tsx`:

### Bar Chart (Recharts)

**Файл:** `front/src/components/charts/bar-chart.tsx`

Категориальный bar chart для grouped результатов (по дням недели, по месяцам и т.д.).

- Библиотека: Shadcn Charts (Recharts) — `front/src/components/ui/chart.tsx`
- Props: `data: Record<string, unknown>[]`, `categoryKey: string`, `valueKey: string`
- Положительные значения — зелёный, отрицательные — красный (oklch)
- Высота: 200px (`h-[200px]`)
- Tooltip с форматированием через `formatValue()`

### Candlestick Chart (lightweight-charts)

**Файл:** `front/src/components/charts/candlestick-chart.tsx`

OHLC candlestick chart с volume histogram на странице инструмента (`/i/:symbol`).

- Библиотека: lightweight-charts v5 (TradingView OSS, ~45KB, canvas)
- Props: `data: OHLCBar[]`
- Up: `#26a69a`, Down: `#ef5350` (TradingView standard)
- Volume: histogram overlay внизу (20% доступной высоты), прозрачные бары
- Высота: 400px (`h-[400px]`)
- Background: transparent (inherits from parent panel). Dark/light: detect `.dark` class, hex colors (zinc palette) for text/grid/crosshair — lightweight-charts не поддерживает CSS variables
- Zoom/pan/crosshair — встроено
- `ResizeObserver` для responsive sizing
- `MutationObserver` на `<html class>` для реактивной смены темы
- Default view: последние ~60 баров (2 месяца)
- Данные обновляются без пересоздания chart (`setData` на существующих series)

### Metrics Grid

**Inline в:** `front/src/components/panels/data-panel.tsx:148-164` (`MetricsGridBlockView`)

4-column grid с ключевыми метриками (используется в backtest results).

- Данные: `block.items: {label, value, color?}[]`
- Layout: `grid-cols-4`, rounded border, `bg-background`
- Цвета: optional `color` (green/red через oklch, или произвольный)

### Area Chart (Recharts)

**Inline в:** `front/src/components/panels/data-panel.tsx:169-218` (`AreaChartBlockView`)

Equity curve + drawdown overlay для backtest results.

- Библиотека: Recharts `ComposedChart` с `Area` и `Line` series
- Данные: `block.x_key`, `block.series: {key, label, style, color}[]`, `block.data[]`
- Высота: 200px (`h-[200px]`)
- Цвета: equity — синий (`oklch(0.65 0.2 250)`), drawdown — красный (`oklch(0.65 0.2 25)`)
- X-axis: tickFormatter показывает только год (`v.slice(0, 4)`)

### Horizontal Bar

**Inline в:** `front/src/components/panels/data-panel.tsx:221-254` (`HorizontalBarBlockView`)

Horizontal bar chart для breakdown распределений (exits в backtest).

- Данные: `block.items: {label, value, detail?}[]`
- Без chart library — pure div-based (rounded bars, `bg-muted` background)
- Ширина: пропорционально `maxAbs` значению
- Цвета: положительные — зелёный, отрицательные — красный (oklch)
- Optional `detail` текст под каждым баром

## Как Bar Chart появляется

Модель не знает о графиках. Процесс:

1. **Backend** (`barb/interpreter.py:634-643`): для `group_by` результатов генерирует chart hint — `{"category": "group_key", "value": "first_value_column"}`
2. **Tool result** (`assistant/chat.py:296-304`): `_build_query_card()` конвертирует hint в typed `bar-chart` block. SSE `data_block` event отправляется в `chat.py:187`.
3. **Frontend** (`data-panel.tsx:273-284`): `switch(block.type)` рендерит `<BarChartBlockView>` когда `block.type === "bar-chart"`
4. Нет hint → нет `bar-chart` block → нет графика. Нет автодетекции по типу данных.

Данные для графика берутся из той же таблицы — без дополнительных API вызовов.

## Data Panel Layout

```
front/src/components/panels/data-panel.tsx
┌─────────────────────────────────────┐
│ [Header]                     [Close]│
│                                     │
│ [Title]                             │
│                                     │
│ [blocks — rendered by type]         │
│   metrics-grid — 4-column KPI grid  │
│   area-chart — equity + drawdown    │
│   horizontal-bar — exits breakdown  │
│   bar-chart — grouped results       │
│   table — full, sortable            │
│                                     │
└─────────────────────────────────────┘
```

- Рендеринг: `switch(block.type)` (`data-panel.tsx:273-284`) — каждый тип → свой компонент
- Таблица: `@tanstack/react-table` с column sorting (dropdown per column)
- Данные: `table_data or source_rows` (Python: `chat.py:285`; table — основной, source_rows — fallback для агрегаций)

## Candlestick Data Flow

1. `GET /api/instruments/{symbol}/ohlc` — все daily bars, без авторизации
2. `useOHLC(symbol)` hook — fetch + localStorage cache
3. `<CandlestickChart data={ohlcData}>` на странице инструмента
