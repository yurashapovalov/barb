# Audit: charts.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 9: "Shadcn Charts (built on Recharts)"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/ui/chart.tsx:2` — `import * as RechartsPrimitive from "recharts"`; `front/package.json:34` — `"recharts": "^2.15.4"`

### Claim 2
- **Doc**: line 13: "Components: Area, Bar, Line charts"
- **Verdict**: WRONG
- **Evidence**: `front/src/components/charts/` contains only `bar-chart.tsx` and `candlestick-chart.tsx`. No Area or Line chart components exist.
- **Fix**: change to "Components: Bar chart (Recharts), Candlestick chart (lightweight-charts)"

### Claim 3
- **Doc**: line 206-207: "Frontend decides chart type automatically based on data structure"
- **Verdict**: WRONG
- **Evidence**: `barb/interpreter.py:629-638` — backend generates `chart` hint; `front/src/components/panels/data-panel.tsx:38-49` — frontend uses backend hint, not auto-detection
- **Fix**: change to "Backend sends chart hints for grouped results. Frontend uses hints to render."

### Claim 4
- **Doc**: line 217: "No backend changes. Backend returns data as usual"
- **Verdict**: WRONG
- **Evidence**: `assistant/tools/__init__.py:68` — returns `"chart": result.get("chart")`; `front/src/types/index.ts:48` — DataBlock includes `chart?`
- **Fix**: update to reflect backend returns `chart` hint field

### Claim 5
- **Doc**: line 218-223: Backend returns `{"summary": {"type": "grouped", "by": "dow", ...}, "table": [...]}`
- **Verdict**: ACCURATE
- **Evidence**: `barb/interpreter.py:694-702` — `summary = {"type": "grouped" if is_grouped else "table", ...}`

### Claim 6
- **Doc**: line 227: "Auto-select chart by summary.type and data structure"
- **Verdict**: WRONG
- **Evidence**: `front/src/components/panels/data-panel.tsx:38-49` — `getChartInfo()` uses `data.chart` (backend hint), not `summary.type`
- **Fix**: change to "Chart selection uses backend chart hint"

### Claim 7
- **Doc**: line 229-234: Frontend logic table mapping grouped + categories -> Bar, grouped + time -> Line, etc.
- **Verdict**: WRONG
- **Evidence**: `front/src/components/panels/data-panel.tsx:32-49` — only `"bar"` type supported, no detection logic
- **Fix**: replace table with "If backend provides chart hint → bar chart. Otherwise no chart."

### Claim 8
- **Doc**: line 238-242: "User can switch chart type with buttons: [Bar] [Line] [Table only]"
- **Verdict**: WRONG
- **Evidence**: no chart switcher exists anywhere in frontend
- **Fix**: remove section or mark as planned

### Claim 9
- **Doc**: line 247-253: Chart components in `front/src/components/ai/charts/`
- **Verdict**: WRONG
- **Evidence**: charts live in `front/src/components/charts/` (not `ai/charts/`). Only `bar-chart.tsx` and `candlestick-chart.tsx`. `data-card.tsx` is a button, not a renderer — `data-panel.tsx` renders charts+tables.
- **Fix**: fix path and file list

### Claim 10
- **Doc**: line 255: "Library: Shadcn Charts (Recharts)"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/charts/bar-chart.tsx:1` — imports from recharts; `front/src/components/ui/chart.tsx` — Shadcn wrapper

### Claim 11
- **Doc**: line 51-76: Histogram chart type
- **Verdict**: WRONG
- **Evidence**: no histogram chart component exists in codebase
- **Fix**: mark as unimplemented

### Claim 12
- **Doc**: line 99-107: Bar chart JSON data format (`chart: "bar"`, `categories`, `values`)
- **Verdict**: WRONG
- **Evidence**: `front/src/components/charts/bar-chart.tsx:13-17` — takes `data: Record<string, unknown>[]`, `categoryKey`, `valueKey`, not categories/values arrays
- **Fix**: update to match actual props

### Claim 13
- **Doc**: line 109-140: Line chart type
- **Verdict**: WRONG
- **Evidence**: no line chart component exists
- **Fix**: mark as unimplemented

### Claim 14
- **Doc**: line 142-174: Equity curve (area chart) for backtest
- **Verdict**: WRONG
- **Evidence**: no equity curve, area chart, or backtest chart exists
- **Fix**: mark as unimplemented

### Claim 15
- **Doc**: line 178: "Charts are built from the same data as tables -- no extra API calls"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/panels/data-panel.tsx:105-107` — chart uses same `rows` as table

### Claim 16
- **Doc**: line 201: "Frontend receives data once, decides how to render"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/panels/data-panel.tsx:105-136` — single data, both chart and table

### Claim 17
- **Doc**: line 259-273: Data Card Layout with Stats Row, collapsible table, "Show N rows"
- **Verdict**: WRONG
- **Evidence**: `front/src/components/panels/data-panel.tsx:118-173` — layout is header → title → optional chart → full table. No stats row, no collapsible table.
- **Fix**: update layout description

### Claim 18
- **Doc**: line 278: "Model does not know about charts"
- **Verdict**: ACCURATE
- **Evidence**: model prompt has no chart mention; `barb/interpreter.py:629-638` generates hints, not the model

### Claim 19
- **Doc**: line 283: "Add Shadcn chart components"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/ui/chart.tsx` exists

### Claim 20
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `front/src/components/charts/candlestick-chart.tsx:1-133` — full candlestick chart using lightweight-charts, not documented
- **Fix**: add CandlestickChart section

### Claim 21
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `barb/interpreter.py:629-638` — backend chart hint mechanism (`{"category": ..., "value": ...}`) not documented
- **Fix**: add backend chart hint section

### Claim 22
- **Doc**: line 307: "Chart height: Fixed 200px or responsive?" (Open Question)
- **Verdict**: OUTDATED
- **Evidence**: `bar-chart.tsx:29` — `h-[200px]`; `candlestick-chart.tsx:132` — `h-[400px]`. Decided.
- **Fix**: remove from Open Questions

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 7 |
| OUTDATED | 1 |
| WRONG | 11 |
| MISSING | 2 |
| UNVERIFIABLE | 0 |
| **Total** | **21** |
| **Accuracy** | **33%** |

## Verification

Date: 2026-02-15

### Claims 1-22 — CONFIRMED

All 22 claims independently verified. All 11 WRONG verdicts confirmed:
- No Area/Line chart components exist
- Backend generates chart hints (not frontend auto-detect)
- No chart type switcher
- Charts in components/charts/, not components/ai/charts/
- Bar chart uses Record<string, unknown>[], not categories/values arrays
- No histogram, line, or equity curve components
- No stats row or collapsible table in data panel

| Result | Count |
|--------|-------|
| CONFIRMED | 22 |
| DISPUTED | 0 |
| INCONCLUSIVE | 0 |
| **Total** | **22** |
