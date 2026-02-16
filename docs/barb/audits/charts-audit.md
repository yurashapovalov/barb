# Audit: charts.md

**Date**: 2026-02-16
**Claims checked**: 30
**Correct**: 27 | **Wrong**: 2 | **Outdated**: 1 | **Unverifiable**: 0

## Issues

### [OUTDATED] interpreter.py line numbers for chart hint generation
- **Doc says**: `barb/interpreter.py:629-638`
- **Code says**: Chart hint code spans lines 630-639 (comment at 630, logic at 631-639)
- **File**: `barb/interpreter.py:630-639`

### [WRONG] data-panel.tsx line numbers for getChartInfo
- **Doc says**: `data-panel.tsx:38-49`
- **Code says**: Function spans lines 38-50 (closing brace at line 50)
- **File**: `front/src/components/panels/data-panel.tsx:38-50`

### [WRONG] useOHLC described as "localStorage cache"
- **Doc says**: `useOHLC(symbol)` hook — fetch + localStorage cache
- **Code says**: Hook uses `readCache`/`writeCache` from `@/lib/cache`, which wraps `localStorage` with a `barb:` prefix and JSON serialization. Calling it "localStorage cache" is technically correct but imprecise — the abstraction layer (`lib/cache.ts`) exists and is the actual API used.
- **File**: `front/src/hooks/use-ohlc.ts:4`, `front/src/lib/cache.ts:1-18`

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Bar chart file: `front/src/components/charts/bar-chart.tsx` | CORRECT | File exists at that path |
| 2 | Bar chart is categorical for grouped results | CORRECT | Used with group_by chart hints; `bar-chart.tsx:19` |
| 3 | Bar chart library: Shadcn Charts (Recharts) via `chart.tsx` | CORRECT | Imports from `recharts` and `@/components/ui/chart`; `bar-chart.tsx:1-7` |
| 4 | Bar chart props: `data: Record<string, unknown>[]`, `categoryKey: string`, `valueKey: string` | CORRECT | `bar-chart.tsx:13-17` |
| 5 | Positive = green, negative = red (oklch) | CORRECT | `COLOR_POSITIVE = "oklch(0.65 0.2 145)"`, `COLOR_NEGATIVE = "oklch(0.65 0.2 25)"`; `bar-chart.tsx:10-11` |
| 6 | Bar chart height: 200px (`h-[200px]`) | CORRECT | `bar-chart.tsx:29` — `className="h-[200px] w-full"` |
| 7 | Tooltip with `formatValue()` | CORRECT | `bar-chart.tsx:46` — `formatter={(value) => formatValue(value, { decimals: 2 })}` |
| 8 | Candlestick file: `front/src/components/charts/candlestick-chart.tsx` | CORRECT | File exists at that path |
| 9 | Candlestick on instrument page `/i/:symbol` | CORRECT | `app.tsx:33-34` route, `instrument-page.container.tsx:18,45`, `instrument-panel.tsx:55` |
| 10 | Library: lightweight-charts v5 (~45KB, canvas) | CORRECT | `package.json:25` — `"lightweight-charts": "^5.1.0"` |
| 11 | Props: `data: OHLCBar[]` | CORRECT | `candlestick-chart.tsx:5-7` |
| 12 | Up: `#26a69a`, Down: `#ef5350` | CORRECT | `candlestick-chart.tsx:60-61` |
| 13 | Volume: histogram overlay at bottom, 20% of height, transparent bars | CORRECT | `scaleMargins: { top: 0.8, bottom: 0 }` = bottom 20%; `rgba(..., 0.3)` = transparent; `candlestick-chart.tsx:68-75,113-115` |
| 14 | Candlestick height: 400px (`h-[400px]`) | CORRECT | `candlestick-chart.tsx:132` — `className="h-[400px] w-full"` |
| 15 | Dark/light: detect `.dark` class, hex colors (zinc palette) | CORRECT | `isDark()` checks `document.documentElement.classList.contains("dark")`; all theme colors are hex from zinc palette; `candlestick-chart.tsx:9-36` |
| 16 | `ResizeObserver` for responsive sizing | CORRECT | `candlestick-chart.tsx:77-81` |
| 17 | `MutationObserver` on `<html class>` for theme changes | CORRECT | `candlestick-chart.tsx:83-86` — observes `document.documentElement` with `attributeFilter: ["class"]` |
| 18 | Default view: last ~60 bars (2 months) | CORRECT | `candlestick-chart.tsx:122-129` — `if (candleData.length > 60) { ... from: candleData.length - 60 }` |
| 19 | Data updates without recreating chart (`setData`) | CORRECT | `candlestick-chart.tsx:118-119` — `candleSeriesRef.current.setData(candleData)` in second `useEffect` |
| 20 | Backend chart hint at `interpreter.py:629-638` | OUTDATED | Code is at lines 630-639; `barb/interpreter.py:630-639` |
| 21 | Chart hint structure: `{"category": "group_key", "value": "first_value_column"}` | CORRECT | `interpreter.py:634,639` — category from group_by, value from first non-group column |
| 22 | Tool result passes hint at `assistant/tools/__init__.py:79` | CORRECT | Line 79: `"chart": result.get("chart")` |
| 23 | Hint in `data_block` SSE event as `chart` field | CORRECT | `chat.py:205` — `"chart": chart_hint` in block dict, emitted as `data_block` event |
| 24 | Frontend `getChartInfo()` at `data-panel.tsx:38-49` | WRONG | Function is at lines 38-50 (closing brace at 50); `data-panel.tsx:38-50` |
| 25 | `getChartInfo` verifies columns exist in data | CORRECT | `data-panel.tsx:43` — `hint.category in rows[0] && hint.value in rows[0]` |
| 26 | No hint = no chart, no autodetection | CORRECT | `data-panel.tsx:49` — returns `null` when no hint |
| 27 | Data for chart from same table, no extra API calls | CORRECT | `data-panel.tsx:105,131` — uses same `rows` for both chart and table |
| 28 | Table: `@tanstack/react-table` with column sorting (dropdown per column) | CORRECT | `data-panel.tsx:1-9,68-84` — DropdownMenu with Ascending/Descending options |
| 29 | Data: `source_rows ?? result` | CORRECT | `data-panel.tsx:105` — `normalizeResult(data.source_rows ?? data.result)` |
| 30 | OHLC endpoint `GET /api/instruments/{symbol}/ohlc`, all daily bars, no auth | CORRECT | `api/main.py:347-367` — no `Depends(get_current_user)`, returns all daily bars |
