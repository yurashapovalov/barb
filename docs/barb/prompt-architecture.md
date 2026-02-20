# Prompt Architecture

Как агент Barb получает знания: system prompt, tool description, function reference.

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────────────┐
│ System Prompt (assistant/prompt/system.py)                         │
│                                                                     │
│  Identity         — "You are Barb..." (2 lines)                    │
│  <instrument>     — symbol, sessions, tick, data range             │
│  <holidays>       — closed/early close days                        │
│  <events>         — FOMC, NFP, OPEX + impact levels                │
│  <data-flow>      — summary vs full table, when to re-query        │
│  <response>       — how to respond (call tool, language, title)     │
│  <limits>         — what to do when feature is missing              │
├─────────────────────────────────────────────────────────────────────┤
│ Tool Descriptions                                                  │
│                                                                     │
│  BARB_TOOL (assistant/tools/__init__.py):                          │
│    Barb Script syntax (fields, execution order, notes)             │
│    Multi-step queries (steps) — filter then compute               │
│    <patterns>     — multi-function patterns (MACD cross, NFP)      │
│    <examples>     — 7 query examples (incl. 2 steps examples)      │
│    <data-protocol>— summary format, "run another query" rule       │
│    <query-rules>  — pct(), period, session, dayname rules          │
│    Expression reference (auto-generated from barb.functions)       │
│      15 function groups, 107 functions                             │
│      compact groups (one line) + expanded groups (with description)│
│                                                                     │
│  BACKTEST_TOOL (assistant/tools/backtest.py):                      │
│    Strategy fields (entry, direction, stop_loss, take_profit, etc) │
│    3 examples (RSI, gap fade, trend following)                     │
│    <analysis-rules> — quality analysis (stability, exits, conc.)   │
│    Same expression syntax as run_query                             │
└─────────────────────────────────────────────────────────────────────┘
```

System prompt — идентичность, data flow, контекст и поведение. Tool description — как пользоваться `run_query` (синтаксис, паттерны, примеры, data protocol, справочник функций) и `run_backtest` (стратегия, примеры, правила анализа). Знание о tool'е живёт рядом с tool'ом — Claude видит всё нужное когда решает вызвать инструмент. Query-specific правила (проценты, сессии, периоды) — в tool description, не в system prompt.

---

## System Prompt

`assistant/prompt/system.py` → `build_system_prompt(instrument: str) -> str`

Вызывается один раз при создании `Assistant`. Результат кэшируется через Anthropic prompt caching (`cache_control: ephemeral`).

### Identity

```
You are Barb — a data interface for {instrument} ({name}).
You translate user questions into tool calls and present results.
```

### Context blocks

Три блока из `assistant/prompt/context.py`. Каждая функция принимает `config: dict` (результат `get_instrument()`), не instrument string.

**`build_instrument_context(config)`** → `<instrument>`:
```xml
<instrument>
Symbol: NQ (Nasdaq 100 E-mini)
Exchange: CME
Data: 2008-01-02 to 2026-02-12
Today: 2026-02-13
Tick: 0.25 ($5.00 per tick, $20.00 per point)
Default session: RTH
All times in ET

Sessions:
  ETH          18:00-17:00
  OVERNIGHT    18:00-09:30
  ...
  RTH          09:30-16:15
</instrument>
```

Включает: point_value (если есть), notes (для rollover предупреждений), `Today: {date.today()}`. Код проверяет `config.get("maintenance")`, но это поле не заполняется (maintenance определяется по gap ETH close → ETH open).

**`build_holiday_context(config)`** → `<holidays>`:
```xml
<holidays>
Market closed: New Year's Day, MLK Day, Presidents Day, ...
Early close: Day before Independence Day (13:15), Black Friday (13:15), ...
Saturday holidays → observed Friday. Sunday → observed Monday.
If user asks about a closed date → tell them why market was closed.
If user asks about early close day → note shortened session.
</holidays>
```

Holidays из `config["holidays"]` (объединено с exchange holidays в `register_instrument()`). Возвращает пустую строку если нет праздников.

**`build_event_context(config)`** → `<events>`:
```xml
<events>
High impact:
  FOMC Rate Decision — 8x/year, 14:00 ET
  Non-Farm Payrolls — 1st Friday, 08:30 ET
  CPI — monthly, 08:30 ET
  PCE — monthly, 08:30 ET

Medium impact: PPI, GDP, Retail Sales, ISM Manufacturing, ISM Services, Consumer Confidence, Michigan Sentiment, Durable Goods Orders

NFP = 1st Friday of month. OPEX = 3rd Friday. Quad Witching = 3rd Fri Mar/Jun/Sep/Dec.
When user asks about event days → calculate dates and query those dates.
</events>
```

События из `get_event_types_for_instrument(symbol)` в `config/market/events.py`. Фильтрует по `EventImpact.HIGH` и `EventImpact.MEDIUM`.

### Behavior

Три секции вместо одного `<behavior>` — каждая про своё:

**`<data-flow>`** — как модель получает данные:
- Модель видит summary (row count, stats, first/last row)
- Пользователь видит полную таблицу в UI
- Для деталей — ещё один запрос

**`<response>`** — как отвечать:
- Data questions → call tool + comment. Knowledge → answer directly
- Язык пользователя
- Confirmation перед вызовом, "title" для UI-карточки
- После результатов — methodology и alternatives

**`<limits>`** — что делать когда функция недоступна:
- Сказать что доступно, предложить альтернативу

Query-specific правила (проценты, сессии, периоды) — в `<query-rules>` внутри tool description. Backtest-specific — в `<analysis-rules>` внутри backtest tool.

---

## Tool Description

`assistant/tools/__init__.py` — `BARB_TOOL` dict.

Inline tool description содержит:
1. Barb Script syntax (все поля с типами)
2. Execution order: `session → period → from → map → where → group_by → select → sort → limit`
3. Important notes (group_by requires column name, select supports aggregates only, pct() for percentages)
4. Multi-step queries (`steps`) — filter then compute, sub-window, breakdown
5. Output format rules — `columns` field for projection, naming conventions
6. `<patterns>` — multi-function patterns (MACD cross, breakout, NFP, OPEX, opening/closing range)
7. `<examples>` — 7 query examples (filter, indicator, raw data, hidden helper, group_by, 2× steps)
8. `<data-protocol>` — explains summary format, "run another query" for details
9. `<query-rules>` — pct(condition), period (ALL if omitted), session (settlement default), dayname()
9. Expression reference (auto-generated)

### Expression Reference

`assistant/tools/reference.py` → `build_function_reference() -> str`

Auto-generated из `barb.functions.SIGNATURES` и `barb.functions.DESCRIPTIONS`. Добавил функцию в код → она появляется в промпте.

Структура:
- Base columns: open, high, low, close, volume
- Operators: arithmetic, comparison, boolean, membership (`in`)
- Functions: 15 групп в `DISPLAY_GROUPS`
- Notes: какие функции берут OHLCV автоматически, NaN handling, dayofweek() = 0-4

### Display Groups

Два формата отображения:

**Compact** (expanded=False) — все сигнатуры на одной строке:
```
Scalar: abs(x), log(x), sqrt(x), sign(x), round(x, n), if(cond, then, else)
Moving Averages: sma(col, n), ema(col, n), wma(col, n), hma(col, n), vwma(n), rma(col, n)
```

**Expanded** (expanded=True) — по строке на функцию с описанием:
```
Oscillators:
  rsi(col, n=14) — Relative Strength Index (Wilder's smoothing)
  stoch_k(n=14) — Stochastic %K (fast)
  ...
```

Compact группы: Scalar, Lag, Moving Averages, Window, Cumulative, Aggregate, Time.
Expanded группы: Pattern, Price, Candle, Signal, Oscillators, Trend, Volatility, Volume.

---

## Chat Integration

`assistant/chat.py` — `Assistant` class.

```python
class Assistant:
    def __init__(self, api_key, instrument, df_daily, df_minute, sessions, model=None):
        self.system_prompt = build_system_prompt(instrument)

    def chat_stream(self, message, history):
        # Streaming response with prompt caching
        self.client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            system=[{"type": "text", "text": self.system_prompt,
                     "cache_control": {"type": "ephemeral"}}],
            tools=[BARB_TOOL, BACKTEST_TOOL],
            messages=messages,
        )
```

- Model: `claude-sonnet-4-5-20250929` (default `MODEL`, overridable via `model` param)
- Max tool rounds: 5 (multi-turn tool use)
- Prompt caching: system prompt cached as ephemeral block
- Two tools: `BARB_TOOL` (run_query) + `BACKTEST_TOOL` (run_backtest)
- Tool dispatch: by `tu["name"]` → `_exec_query()` or `_exec_backtest()`
- Dataframe selection: run_query — intraday/RTH → df_minute, else → df_daily. run_backtest — always df_minute (engine resamples to daily)
- Tool results: `model_response` (summary) goes to Claude, data block goes to UI
- Cost accounting: per-call token usage + cost breakdown (Sonnet 4.5 pricing) in `done` event

---

## Data Sources

### Supabase: таблица `exchanges`

```
code        text PK       — CME, CBOT, NYMEX, COMEX, ICEEUR, ICEUS, EUREX
name        text          — Chicago Mercantile Exchange
timezone    text          — CT, ET, GMT
image_url   text          — (optional)
```

ETH и maintenance удалены из exchanges: ETH перенесен в instrument config.sessions (варьируется per-instrument), maintenance определяется по gap между ETH close и ETH open.

### Supabase: таблица `instruments`

```
symbol          text PK       — NQ, ES, CL, FDAX
name            text          — Nasdaq 100 E-mini
exchange        text FK       — → exchanges.code
type            text          — futures
category        text          — index, energy, metals, currency, ...
currency        text          — USD, EUR
default_session text          — RTH (SQL default)
data_start      date          — 2008-01-02
data_end        date          — 2026-02-12
events          text[]        — {macro, options}
notes           text          — AI context (rollover offsets)
image_url       text          — (UI only)
active          boolean       — (UI only)
config          jsonb         — {tick_size, tick_value, point_value, sessions}
```

### Supabase: view `instrument_full`

```sql
select
  i.symbol, i.name, i.exchange, i.type, i.category, i.currency,
  i.default_session, i.data_start, i.data_end, i.events, i.notes, i.config,
  e.timezone as exchange_timezone, e.name as exchange_name
from instruments i join exchanges e on i.exchange = e.code
```

Без image_url, active (не нужны модели).

### config/market/

- `instruments.py` — `get_instrument(symbol)`: cache lookup. `register_instrument(row)` normalizes Supabase rows + merges exchange holidays at API startup
- `holidays.py` — `EXCHANGE_HOLIDAYS` dict, `HOLIDAY_NAMES`, `get_holidays_for_year()`
- `events.py` — `get_event_types_for_instrument()`, `EventImpact.HIGH/MEDIUM`

### Data files

```
data/1d/futures/{symbol}.parquet   — дневные бары (settlement close)
data/1m/futures/{symbol}.parquet   — минутные бары (для интрадей)
```

`barb/data.py` → `load_data(instrument, timeframe, asset_type)`: timeframe — literal directory name ("1d" or "1m"). Routing logic (query timeframe → which dataset) lives in `assistant/chat.py`.

---

## Auto-generation Chain

### Functions → Tool Reference → Claude

```
barb/functions/oscillators.py          assistant/tools/reference.py     Claude sees:
┌───────────────────────────┐         ┌──────────────────────┐        ┌──────────────────┐
│ OSCILLATOR_SIGNATURES={   │         │ build_function       │        │ Oscillators:     │
│   "rsi":"rsi(col,n=14)",  │ ──────  │   _reference()       │ ─────  │  rsi(col,n=14)   │
│   "cci":"cci(n=20)",      │         │                      │        │   — Relative     │
│ }                         │         │ reads SIGNATURES +   │        │   Strength Index │
│ OSCILLATOR_DESCRIPTIONS={ │         │ DESCRIPTIONS from    │        │  cci(n=20) — ... │
│   "rsi":"Relative...",    │         │ barb.functions       │        └──────────────────┘
│ }                         │         └──────────────────────┘
└───────────────────────────┘
```

Добавил функцию в `barb/functions/` → SIGNATURES + DESCRIPTIONS → `build_function_reference()` → tool description → Claude знает.

### Market Context → System Prompt → Claude

```
Supabase instruments              config/market/           assistant/prompt/
┌─────────────────────┐          ┌──────────────────┐    ┌────────────────────┐
│ instrument_full     │          │ holidays.py      │    │ context.py:        │
│  NQ: sessions,      │──┐      │ events.py        │──┐ │  build_instrument  │
│  ticks, events      │  │      │ instruments.py   │  │ │  build_holiday     │
└─────────────────────┘  │      └──────────────────┘  │ │  build_event       │
                         └────────────┬───────────────┘ └────────┬───────────┘
                                      │                           │
                              get_instrument("NQ")      build_system_prompt("NQ")
                              merges config + holidays   produces complete prompt
```

INSERT instrument в Supabase → context auto-generated → Claude знает.

---

## File Structure

```
assistant/
  prompt/
    __init__.py           — exports build_system_prompt
    system.py             — build_system_prompt() (identity, context, data-flow, response, limits)
    context.py            — build_instrument/holiday/event_context(config)
  tools/
    __init__.py           — BARB_TOOL dict, run_query(), _format_summary_for_model()
    backtest.py           — BACKTEST_TOOL dict, run_backtest_tool(), _format_summary()
    reference.py          — build_function_reference(), DISPLAY_GROUPS
  chat.py                 — Assistant class, chat_stream(), tool dispatch, prompt caching
```

### Dependencies

```
prompt/system.py  ← config/market/instruments.py (get_instrument)
                  ← prompt/context.py  ← config/market/holidays.py (HOLIDAY_NAMES)
                                       ← config/market/events.py (get_event_types, EventImpact)

tools/__init__.py ← tools/reference.py ← barb/functions (SIGNATURES + DESCRIPTIONS)
                  ← barb/interpreter    (execute)
                  ← barb/ops            (BarbError)

tools/backtest.py ← barb/backtest      (run_backtest, Strategy, BacktestMetrics)

chat.py           ← prompt/__init__.py  (build_system_prompt)
                  ← tools/__init__.py   (BARB_TOOL, run_query)
                  ← tools/backtest.py   (BACKTEST_TOOL, run_backtest_tool)
```
