# Charts & Visualizations

Графики дополняют таблицы. Некоторые паттерны проще увидеть на графике чем в числах.

## Компоненты

Два типа графиков, две разные библиотеки:

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
- Dark/light: detect `.dark` class, hex colors (zinc palette) — lightweight-charts не поддерживает CSS variables
- Zoom/pan/crosshair — встроено
- `ResizeObserver` для responsive sizing
- `MutationObserver` на `<html class>` для реактивной смены темы
- Default view: последние ~60 баров (2 месяца)
- Данные обновляются без пересоздания chart (`setData` на существующих series)

## Как Bar Chart появляется

Модель не знает о графиках. Процесс:

1. **Backend** (`barb/interpreter.py:630-639`): для `group_by` результатов генерирует chart hint — `{"category": "group_key", "value": "first_value_column"}`
2. **Tool result** (`assistant/tools/__init__.py:79`): hint передаётся в `data_block` SSE event как поле `chart`
3. **Frontend** (`data-panel.tsx:38-50`): `getChartInfo()` проверяет hint — если `category` и `value` колонки существуют в данных → рендерит `<BarChart>`
4. Нет hint → нет графика. Нет автодетекции по типу данных.

Данные для графика берутся из той же таблицы — без дополнительных API вызовов.

## Data Panel Layout

```
front/src/components/panels/data-panel.tsx
┌─────────────────────────────────────┐
│ [Header]                     [Close]│
│                                     │
│ [Title]                             │
│                                     │
│ [Bar Chart — if chart hint exists]  │
│                                     │
│ [Table — full, sortable]            │
│                                     │
└─────────────────────────────────────┘
```

- Таблица: `@tanstack/react-table` с column sorting (dropdown per column)
- Данные: `source_rows ?? result` (агрегации показывают исходные строки)

## Candlestick Data Flow

1. `GET /api/instruments/{symbol}/ohlc` — все daily bars, без авторизации
2. `useOHLC(symbol)` hook — fetch + localStorage cache
3. `<CandlestickChart data={ohlcData}>` на странице инструмента
