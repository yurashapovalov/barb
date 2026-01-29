# Barb Assistant — Architecture

How the AI assistant works: prompt structure, tools, and data flow.

---

## 1. Overview

Barb Assistant is an AI-powered trading data analyst. The user asks questions in natural language, the assistant analyzes data and responds with insights.

```
User question
    → LLM (with lightweight system prompt + tools)
        → understands question
        → explains what it will compute
        → user confirms
        → calls execute_query tool
    → Interpreter executes Barb Script query
    → Result (number + metadata)
    → LLM formulates human answer
    → UI shows answer + table/graph as proof
```

The LLM is the brain. Barb Script is the hands. The interpreter is deterministic — all intelligence is in the LLM.

**Key design principle:** The system prompt stays small. Everything the LLM needs to know *on demand* lives in tools. The prompt only contains what's needed for *every* response. This keeps latency low and scales as Barb grows.

---

## 2. System Prompt — Minimal Core

The system prompt contains only what the LLM needs for every interaction. ~30 lines, always fast.

```
System Prompt (always loaded)
├── role            — who you are (3 lines)
├── instrument      — current instrument context (15 lines)
└── rules           — behavioral guidelines (6 lines)
```

Everything else — query format, functions, indicators, events, examples — is available through tools. The LLM pulls what it needs, when it needs it.

### 2.1 role

```
You are Barb — a trading data analyst assistant.
You answer questions about market data by computing statistics
from historical OHLCV bars using the Barb Script query language.
You have tools to execute queries and look up reference information.
```

### 2.2 instrument

**Dynamic.** Generated from instrument config at runtime.

```
Current instrument: NQ (Nasdaq 100 E-mini)
Exchange: CME
Data: 2008-01-02 to 2026-01-07
Timezone: ET

Sessions:
  ETH (full day):    18:00 — 17:00
  OVERNIGHT:         18:00 — 09:30
    ASIAN:           18:00 — 03:00
    EUROPEAN:        03:00 — 09:30
  RTH:               09:30 — 17:00
    RTH_OPEN:        09:30 — 10:30
    MORNING:         09:30 — 12:30
    AFTERNOON:       12:30 — 17:00
    RTH_CLOSE:       16:00 — 17:00

Default session: RTH
Maintenance break: 17:00 — 18:00 (no trading)
```

This stays in the prompt because the LLM needs sessions and data range context for every analytical question. When the instrument changes (NQ → ES → CL), only this part changes.

### 2.3 rules

```
1. Before executing a query, explain what you will compute.
   Mention: metric, timeframe, session, period. Ask for confirmation.
2. After getting the result, give a clear answer with the number
   and context (how many bars, what period).
3. If a query returns an error, read the error, fix the query, retry once.
4. Use indicators proactively when they add value.
5. For daily+ timeframes, always specify session.
6. Default to all available data unless user specifies a period.
```

6 rules. Not 60. Tools and examples do the heavy lifting.

### 2.4 Total prompt size

~30 lines. Fast for every response, including simple questions like "привет" or "что такое inside day?".

---

## 3. Tools

The LLM has access to tools via standard function calling (OpenAI / Anthropic tool use). Tools provide everything that's not in the system prompt.

### 3.1 execute_query

The primary tool. Executes a Barb Script query and returns the result.

```json
{
  "name": "execute_query",
  "description": "Execute a Barb Script query on historical OHLCV data.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "object",
        "description": "Barb Script JSON query"
      }
    },
    "required": ["query"]
  }
}
```

**Returns:**

```json
{
  "result": 45.3,
  "metadata": {
    "rows": 4521,
    "period": "2008-01-02 — 2026-01-07",
    "session": "RTH",
    "from": "daily",
    "warnings": []
  }
}
```

LLM sees `result` + `metadata`. UI separately receives `table` + `query` for display.

**On error:**

```json
{
  "error": true,
  "error_type": "UnknownColumn",
  "message": "Column 'rnage' does not exist. Available: open, high, low, close, volume, range",
  "step": "where"
}
```

LLM reads the error, fixes the query, calls again.

### 3.2 get_query_reference

Reference tool. Returns everything the LLM needs to build a query: format, functions, examples. The LLM calls this before building its first query in a conversation (or when unsure about syntax).

```json
{
  "name": "get_query_reference",
  "description": "Get Barb Script query format, available functions, and examples. Call this before building a query.",
  "parameters": {
    "type": "object",
    "properties": {}
  }
}
```

**Returns:**

```
QUERY FORMAT:
JSON object with optional fields:
- session: string — session name (required for daily+ timeframes)
- from: string — 1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly
- period: string — "2024", "2024-01", "2024-01-01:2024-12-31", "last_year", "last_month"
- join: {source, filter} — external data
- map: {name: expression} — computed columns (simple steps, 1-2 operations each)
- where: string — row filter
- group_by: string | list — grouping
- select: string | list — aggregation
- sort: string — "column [asc|desc]"
- limit: int — max rows

FUNCTIONS:
Scalar: abs(x), log(x), sqrt(x), sign(x), round(x, n), if(cond, then, else)
Lag: prev(col), prev(col, n), next(col), next(col, n)
Window: rolling_mean(col, n), rolling_sum(col, n), rolling_max(col, n),
        rolling_min(col, n), rolling_std(col, n), rolling_count(cond, n), ema(col, n)
Cumulative: cummax(col), cummin(col), cumsum(col)
Pattern: streak(cond), bars_since(cond), rank(col)
Aggregate: mean(col), sum(col), max(col), min(col), std(col), median(col),
           count(), percentile(col, p), correlation(col1, col2)
Time: dayofweek(), hour(), month(), year(), date(), day(), quarter()
Session: session_open(s), session_high(s), session_low(s), session_close(s), session_volume(s)

EXAMPLES:
[10 question → query pairs, same as before]
```

This is ~200 lines. The LLM reads it once, caches in context, and builds queries for the rest of the conversation. Not loaded for non-analytical questions.

### 3.3 get_indicators

Returns available indicators. The LLM calls this when the question involves technical analysis or when it wants to proactively suggest indicators.

```json
{
  "name": "get_indicators",
  "description": "Get available technical indicators with signatures, defaults, and usage.",
  "parameters": {
    "type": "object",
    "properties": {}
  }
}
```

**Returns:**

```
INDICATORS:
- rsi(col, n) — Relative Strength Index. Default: rsi(close, 14). >70 overbought, <30 oversold.
- macd(col, fast, slow, signal) — MACD. Default: macd(close, 12, 26, 9).
- bollinger(col, n, std) — Bollinger Bands. Default: bollinger(close, 20, 2).
- stochastic(k, d, slowing) — Default: stochastic(14, 3, 3).
- atr(n) — Average True Range. Default: atr(14).
- adx(n) — Average Directional Index. Default: adx(14). Trend strength 0-100.
- cci(n) — Commodity Channel Index. Default: cci(20).
- mfi(n) — Money Flow Index. Default: mfi(14). Volume-weighted RSI.
- obv() — On-Balance Volume.
- vwap() — Volume-Weighted Average Price.
- keltner(n, atr_n, mult) — Keltner Channels. Default: keltner(20, 10, 1.5).
- donchian(n) — Donchian Channels. Default: donchian(20).

Each indicator expands into primitive steps. Use in map expressions.
```

### 3.4 get_events

Returns available market events. The LLM calls this when the question involves events or when suggesting event-based analysis.

```json
{
  "name": "get_events",
  "description": "Get available market events for the current instrument.",
  "parameters": {
    "type": "object",
    "properties": {}
  }
}
```

**Returns:**

```
EVENTS (use with join):
- fomc — FOMC Rate Decision (macro, high impact)
- nfp — Non-Farm Payrolls (macro, high impact)
- cpi — Consumer Price Index (macro, high impact)
- opex — Monthly Options Expiration (options, medium impact)
- quad_witching — Quarterly Options Expiration (options, high impact)
```

---

## 4. How It Scales

### 4.1 Adding new capabilities

| What's new | What changes |
|------------|-------------|
| New instrument (ES, CL) | `instrument` component in prompt (auto from config) |
| New function in Barb Script | `get_query_reference` tool returns updated list |
| New indicator | `get_indicators` tool returns updated list |
| New event type | `get_events` tool returns updated list |
| New tool (backtest, news) | Add new tool definition. Prompt doesn't change. |
| Better examples | Update `get_query_reference` return. Prompt doesn't change. |
| Different LLM model | Potentially different prompt variant (section 6) |

**The system prompt almost never changes.** New capabilities = new tools or updated tool responses. This is the Cline pattern — and why it works long-term.

### 4.2 Growth path

```
Now:
  Tools: execute_query, get_query_reference, get_indicators, get_events

Later:
  Tools: execute_query, get_query_reference, get_indicators, get_events,
         execute_backtest, get_strategies, get_news, compare_instruments,
         save_analysis, get_watchlist, ...
```

Each new tool is independent. No prompt rewrite. No "переделывать постоянно".

---

## 5. Conversation Flow

### 5.1 Simple question (no query needed)

```
User: "что такое inside day?"

System prompt: ~30 lines (role + instrument + rules)
Tools called: none
LLM: explains from its own knowledge
Latency: fast
```

### 5.2 Analytical question (query needed)

```
User: "какой средний range по дням недели?"

1. LLM reads question
2. LLM calls get_query_reference (first time only — cached in context after)
3. LLM explains: "Посчитаю средний RTH range по дням недели за всё время"
4. User confirms
5. LLM calls execute_query with Barb Script JSON
6. Interpreter returns result + metadata
7. LLM: "Самый волатильный день — среда (48.2 пунктов)..."
8. UI shows table + graph
```

### 5.3 Error recovery

```
1. LLM calls execute_query
2. Interpreter returns error with message
3. LLM reads error, fixes query, retries once
4. If still fails — tells user what went wrong
```

### 5.4 Multi-query analysis

```
User: "сравни объём в дни FOMC и обычные дни"

LLM:
  1. calls get_events (if first time)
  2. calls execute_query → FOMC days volume
  3. calls execute_query → all days volume
  4. Compares and answers
```

The LLM decides how many queries to run. No orchestration — tool calling handles it.

### 5.5 Proactive insights

```
User: "какой средний range?"

LLM computes range, then proactively:
  1. calls get_indicators
  2. calls execute_query → current ATR
  3. "Средний RTH range — 45.3 пт. ATR(14) сейчас 52.1 — волатильность выше среднего."
```

---

## 6. Future: Model Variants

Different LLM models may need different prompt variants (like Cline does). For now, one prompt works. When needed:

```
variants/
├── default.py      — works for Claude, GPT-4
├── small.py        — optimized for smaller models (shorter prompt, simpler)
└── reasoning.py    — for reasoning models (less hand-holding)
```

Each variant can override prompt components. The assembly logic picks the right variant.

Not needed now. Architecture supports it when needed.
