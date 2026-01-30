# LLM Requirements

What the LLM must do to correctly translate a user question into a Barb Script query.

---

## 1. Role

The LLM is the bridge between natural language and structured query. It does NOT execute anything — it produces a JSON query that the interpreter executes.

Two stages:
1. **Understand** — explain to the user what will be computed, get confirmation
2. **Generate** — produce a Barb Script JSON query

---

## 2. What the LLM must determine

For every analysis question, the LLM must choose:

### 2.1 Frame (what data to look at)

| Parameter | What to decide | Default assumption |
|-----------|---------------|-------------------|
| **Period** | Which date range? | All available data |
| **Timeframe** | What bar size? | `daily` |
| **Session** | What hours of the day? | Default from instrument config (e.g., RTH for NQ) |

The LLM must infer these from context. The user rarely says all three explicitly.

### 2.2 Computation (what to calculate)

| Parameter | What to decide |
|-----------|---------------|
| **Metrics** | What to measure (range, volume, gap, etc.) |
| **Conditions** | What to filter by (inside day, gap up, FOMC, etc.) |
| **Grouping** | How to break down (by weekday, month, year, etc.) |
| **Aggregation** | How to summarize (mean, count, percentage, etc.) |

### 2.3 Output

| Parameter | What to decide |
|-----------|---------------|
| **Format** | Single number, table, or comparison |
| **Sort** | What order |
| **Limit** | How many rows |

---

## 3. Inference rules

These are NOT hardcoded rules. They are guidelines for the LLM to make reasonable defaults when the user is ambiguous.

### 3.1 Timeframe inference

The timeframe depends on the nature of the question, not on specific keywords.

| User intent | Likely timeframe | Why |
|-------------|-----------------|-----|
| "Average range", "volume by weekday", "inside days" | daily | These are daily concepts. Range = daily range. |
| "What happens in the first hour" | Depends. Session filter on minute data, then resample to daily per-day. Or hourly bars. Depends on what metric. |
| "Volume profile by hour" | 1h or 1m grouped by hour | Need hourly resolution |
| "5-minute candle patterns" | 5m | Explicit timeframe |
| "Weekly trend" | weekly | Explicit timeframe |
| "Monthly seasonality" | daily grouped by month | Daily bars, grouped by month |

Key principle: **the timeframe is whatever produces the bars that the metric is computed on.** "Daily range" = range of daily bars. "Hourly volume" = volume of hourly bars.

### 3.2 Session inference

| User intent | Likely session | Why |
|-------------|---------------|-----|
| No mention of session | Default from config (RTH for NQ) | Most analysis is about regular hours. TradingView shows RTH. |
| "Overnight", "after hours" | OVERNIGHT | Explicit |
| "Pre-market", "Asian session" | ASIAN or EUROPEAN | Explicit |
| "Full day", "24 hours", "ETH" | ETH | Explicit |
| "First hour", "opening" | RTH_OPEN | First hour of RTH |
| "Last hour", "close" | RTH_CLOSE | Last hour of RTH |
| "Morning" | MORNING | Morning RTH |

Key principle: **if the user doesn't mention a session, assume the default.** The default is what the user sees on their chart (typically RTH).

### 3.3 Period inference

| User intent | Likely period | Why |
|-------------|--------------|-----|
| No mention of time | All data | Larger sample = more reliable statistics |
| "Last year", "this year" | Filter by year | Explicit |
| "In 2024" | Filter: year == 2024 | Explicit |
| "Last month" | Filter: last 30 days | Explicit |
| "Recently" | Ambiguous — ask user or use last year | |

---

## 4. Understanding stage requirements

Before generating a query, the LLM must explain what it will do. This explanation must include:

### 4.1 Must mention explicitly

- **What metric** will be computed (e.g., "range", "volume", "gap fill percentage")
- **What timeframe** (e.g., "daily bars", "15-minute bars")
- **What session** if daily+ (e.g., "RTH", "full trading day")
- **What filter** if any (e.g., "only inside days", "only FOMC days")
- **What grouping** if any (e.g., "by day of week", "by month")
- **What period** if not all data (e.g., "for 2024", "last year")

### 4.2 Example

User: "какой средний range по дням недели?"

Good response: "Посчитаю средний дневной range (high - low) RTH-баров за всё время, с разбивкой по дням недели. Верно?"

This mentions: metric (range), timeframe (daily), session (RTH), period (all), grouping (weekday).

Bad response: "Посчитаю средний range по дням недели. Верно?"

Missing: timeframe, session, period. User confirms but doesn't know what exactly will be computed.

### 4.3 Ambiguity handling

When the question is ambiguous, the LLM should:
1. Choose the most likely interpretation
2. State it explicitly in the confirmation
3. The user will correct if wrong

Do NOT ask multiple clarifying questions. Make a decision, state it, let the user adjust.

---

## 5. Generation stage requirements

After user confirms, the LLM generates a Barb Script JSON query.

### 5.1 Query must be valid

- All fields must match the spec
- `from` must be one of the 12 valid timeframes
- `session` must be a session name from the instrument config
- All column references in expressions must be defined (base columns or in `map`)
- All function names must be from the catalog

### 5.2 Query must match the confirmation

What the LLM told the user must match what the query does. If the LLM said "RTH daily range" but the query doesn't have `session: "RTH"` — that's a bug.

### 5.3 Use catalog metrics

Prefer named metrics from the catalog over raw expressions:
- Good: `"range"` (known concept)
- Avoid: `"high - low"` (raw formula, same thing but less readable)

The interpreter knows how to compute catalog metrics. Raw expressions are allowed but should be the exception.

---

## 6. Knowledge the LLM needs

The LLM must be provided with:

1. **Instrument config** — sessions, trading hours, timezone
2. **Available data range** — start and end dates
3. **Catalog of metrics** — all named metrics with descriptions
4. **Catalog of conditions** — all named patterns
5. **Available events** — FOMC, NFP, OPEX, etc.
6. **Glossary** — trading terms (IB, NR7, gap fill, etc.)
7. **Query format** — Barb Script JSON spec
8. **Current date** — for relative periods ("last year", "this month")

---

## 7. Common mistakes to avoid

| Mistake | Example | Why it's wrong |
|---------|---------|---------------|
| Forgetting session for daily+ | `{"from": "daily", "select": "mean(range)"}` | Which daily bar? RTH or full day? |
| Wrong timeframe for the question | "Daily range" → `from: "1h"` | Range of hourly bars != daily range |
| Using raw formulas instead of catalog | `"high - low"` instead of `"range"` | Less readable, more room for error |
| Not mentioning timeframe in confirmation | "Посчитаю range" | User doesn't know if daily or hourly |
| Over-complicating | Using multiple map steps when one metric suffices | Keep it simple |
| Assuming period | User said "range" → LLM picks "last year" | Default is all data unless user specified |
