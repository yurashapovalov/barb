# Charts & Visualizations

## Overview

Charts complement tables for data understanding. Some insights are easier to grasp visually than from numbers. Charts appear alongside tables in the same data card.

## Technology

**Shadcn Charts** (built on Recharts)
- Already in the stack (shadcn/ui)
- Consistent styling with the app
- Dark mode support out of the box
- Components: Area, Bar, Line charts

Reference: https://ui.shadcn.com/charts

## User Experience

```
User: "Покажи распределение дневных изменений за 2024"

Barb: Строю распределение...

[Data Card: "Распределение дневных изменений 2024"]
┌─────────────────────────────────────────┐
│  [Histogram]                            │
│       ▄▄                                │
│      ████                               │
│     ██████                              │
│    ████████▄                            │
│  ▄██████████▄▄                          │
│ -3% -2% -1%  0% +1% +2% +3%             │
├─────────────────────────────────────────┤
│ Mean: +0.05%  Std: 1.2%  Skew: -0.3     │
│ [Table: 251 rows]  [Expand]             │
└─────────────────────────────────────────┘
```

## Query → Chart Mapping

| Query Type | Example | Chart |
|------------|---------|-------|
| Single aggregation | `select: "count()"` | None (just number) |
| Table without group_by | List of rows | None (or histogram if asked) |
| `group_by: "dayname()"` | Stats by weekday | **Bar chart** |
| `group_by: "month()"` | Stats by month | **Bar chart** or **Line chart** |
| `group_by: "year()"` | Multi-year trend | **Line chart** |
| "распределение X" | Distribution | **Histogram** (bar chart) |
| Backtest results | Trades + P&L | **Equity curve** (area chart) |

## Chart Types (v1)

### 1. Histogram (Distribution)

**Use case:** Understanding spread of values

**Triggers:**
- "распределение гэпов"
- "distribution of daily ranges"
- Queries with many numeric results

**Data needed:**
```json
{
  "chart": "histogram",
  "values": [0.5, -1.2, 0.8, ...],
  "bins": 20,
  "xlabel": "Daily Change %",
  "stats": {
    "mean": 0.05,
    "std": 1.2,
    "skew": -0.3,
    "kurtosis": 4.2
  }
}
```

### 2. Bar Chart (Categories)

**Use case:** Comparing values across categories

**Triggers:**
- "по дням недели"
- "by month"
- `group_by` queries

**Example:**
```
"Средний рейндж по дням недели"

[Bar Chart]
Mon  ████████ 156
Tue  ██████████ 178
Wed  ████████████ 195
Thu  █████████ 168
Fri  ███████ 142
```

**Data needed:**
```json
{
  "chart": "bar",
  "categories": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "values": [156, 178, 195, 168, 142],
  "ylabel": "Average Range (pts)"
}
```

### 3. Line Chart (Time Series)

**Use case:** Trends over time

**Triggers:**
- "по месяцам"
- "trend over time"
- Temporal groupings

**Example:**
```
"Средний объём по месяцам 2024"

[Line Chart]
Volume
  │    ╭─╮
  │ ╭──╯  ╰──╮    ╭─
  │─╯        ╰────╯
  └─────────────────
   J F M A M J J A S O N D
```

**Data needed:**
```json
{
  "chart": "line",
  "x": ["2024-01", "2024-02", ...],
  "y": [1250000, 1180000, ...],
  "xlabel": "Month",
  "ylabel": "Avg Volume"
}
```

### 4. Equity Curve (Backtest)

**Use case:** Visualize strategy performance over time

**Triggers:**
- Backtest results
- Always shown with backtest

**Example:**
```
[Equity Curve]
P&L
+800 │              ╭────
+600 │         ╭────╯
+400 │    ╭────╯
+200 │ ╭──╯
   0 │─╯
-200 │
     └─────────────────────
      Jan  Feb  Mar  Apr  May
```

**Data needed:**
```json
{
  "chart": "equity",
  "dates": ["2024-01-15", "2024-01-22", ...],
  "cumulative_pnl": [50, 30, 80, 120, ...],
  "drawdown_periods": [
    {"start": "2024-02-01", "end": "2024-02-15", "depth": -85}
  ]
}
```

## Data Source

Charts are built from the **same data as tables** — no extra API calls.

**Histogram (distribution):**
```
Table: [date, change_pct, volume, ...]  ← 251 rows
Chart: take change_pct column → build histogram
```

**Bar chart (categories):**
```
Table:
  Mon | 156
  Tue | 178
  Wed | 195
Chart: same 5 rows → 5 bars
```

**Equity curve (backtest):**
```
Table: [date, entry, exit, pnl, ...]  ← trades
Chart: cumsum(pnl) → area chart
```

Frontend receives data once, decides how to render (table, chart, or both).

## Architecture

### Decision: Frontend decides chart type

Модель НЕ указывает тип графика. Фронт решает автоматически по структуре данных.

**Почему:**
- Модель может ошибиться с выбором
- Пользователь хочет переключить → нужен повторный API call
- Усложняет промпт
- Данные уже есть на фронте — перерисовка мгновенная

### Backend Changes

Никаких изменений в tool schema. Backend возвращает данные как обычно:
```python
{
  "summary": {"type": "grouped", "by": "dow", ...},
  "table": [...],
}
```

### Frontend Logic

Автовыбор графика по `summary.type` и структуре данных:

| Условие | График |
|---------|--------|
| `type: "grouped"` + категории (dow, dayname) | Bar |
| `type: "grouped"` + время (month, year) | Line |
| `type: "table"` + числовая колонка | Histogram (опционально) |
| `type: "scalar"` или `type: "dict"` | Нет графика |

### User Override

Пользователь может переключить тип графика кнопками:
```
[Bar] [Line] [Table only]
```
Данные не перезапрашиваются — мгновенная перерисовка.

### Frontend Components

```
front/src/components/ai/
  charts/
    bar-chart.tsx      # Histogram + category bars
    line-chart.tsx     # Trends over time
    area-chart.tsx     # Equity curve
  data-card.tsx        # Updated to render chart + table
```

**Library:** Shadcn Charts (Recharts)
- `npx shadcn@latest add chart` to add base components
- Customize colors to match app theme

### Data Card Layout

```
┌─────────────────────────────────────┐
│ [Title]                             │
├─────────────────────────────────────┤
│                                     │
│  [Chart Area - if present]          │
│                                     │
├─────────────────────────────────────┤
│ [Stats Row - key metrics]           │
├─────────────────────────────────────┤
│ [Table - collapsible]               │
│ ▼ Show 17 rows                      │
└─────────────────────────────────────┘
```

## Prompt Updates

Не требуется. Модель не знает о графиках — фронт решает сам.

## Implementation Plan

### Step 1: Basic Charts (auto-selected)
- [ ] Add Shadcn chart components (`npx shadcn@latest add chart`)
- [ ] Create chart components in `components/ai/charts/`
- [ ] Update DataCard: detect data type → show default chart
- [ ] Bar chart for grouped categorical data
- [ ] Line chart for grouped temporal data

### Step 2: Chart Switcher
- [ ] Add chart type buttons to DataCard header
- [ ] Store selected chart type in component state
- [ ] Instant re-render on switch (no API call)

### Step 3: Additional Charts
- [ ] Histogram for distributions
- [ ] Area chart (equity curve) for backtests

## Deferred (v2+)

- Scatter plots (correlation)
- Candlestick charts (pattern visualization)
- Interactive drill-down (click bar → see details)
- Export chart as image

## Open Questions

1. **Chart height:** Fixed 200px or responsive?
2. **Mobile:** Stack chart above table?
