# Prompt Architecture

Как агент Barb получает знания и как они масштабируются.

---

## Проблема

Текущий `prompt.py` — 97 строк. Claude не знает:
- Какие функции доступны в expressions
- Синтаксис Barb Script (9 шагов пайплайна)
- Как строить сложные запросы
- Какие индикаторы есть и как их вызывать
- Что рынок закрыт на Рождество
- Что NFP выходит в первую пятницу месяца
- Что "перепродан" = RSI < 30

С ростом системы добавятся: 107 функций (Phase 1), backtest (Phase 2), screener (Phase 3), multi-instrument (Phase 4). Всё это нужно донести до Claude — но не монолитом.

---

## Пять слоёв знаний агента

```
┌──────────────────────────────────────────────────────┐
│ 1. IDENTITY         Кто я, как себя вести            │  ← статический
├──────────────────────────────────────────────────────┤
│ 2. MARKET CONTEXT   Инструмент, сессии, праздники,   │  ← динамический
│                     ивенты, point value               │    (из config/)
├──────────────────────────────────────────────────────┤
│ 3. TRADING KNOWLEDGE  "перепродан" → RSI < 30        │  ← экспертный
│                       "волатильность" → ATR            │
│                       "тренд" → ADX > 25              │
├──────────────────────────────────────────────────────┤
│ 4. TOOL: run_query    Синтаксис, функции, примеры    │  ← автогенерация
├──────────────────────────────────────────────────────┤
│ 5. ANNOTATIONS        Праздники/ивенты в результатах │  ← автоматический
│                       "Dec 24: early close (13:15)"  │    пост-процессинг
├──────────────────────────────────────────────────────┤
│ 6. TOOL: run_backtest / run_screener  (Phase 2-3)    │  ← будущее
└──────────────────────────────────────────────────────┘
```

Слои 1-3 живут в **system prompt**. Слой 4 и 6 — в **tool descriptions**. Слой 5 — в **tool results** (автоматический пост-процессинг).

---

## Где что живёт

### System Prompt — контекст и поведение

```
┌─────────────────────────────────────────┐
│ System Prompt                           │
│                                         │
│  Identity         — "You are Barb"      │  статический
│  Instrument       — NQ, сессии, TZ      │  из instruments.py
│  Holidays         — closed/early close  │  из holidays.py
│  Events           — FOMC, NFP, OPEX     │  из events.py
│  Trading Knowledge — concept → indicator│  экспертный маппинг
│  Behavior         — format, language    │  статический
│  Examples         — conversation flow   │  статический
│                                         │
│  ~1,500 tokens                          │
└─────────────────────────────────────────┘
```

### Tool Description — как пользоваться инструментом

```
┌─────────────────────────────────────────┐
│ Tool: run_query                         │
│                                         │
│  Syntax       — Barb Script JSON schema │  статический
│  Functions    — 107 signatures          │  из FUNCTIONS dict
│  Patterns     — query JSON examples     │  статический
│                                         │
│  ~2,500 tokens                          │
└─────────────────────────────────────────┘
```

### Почему не всё в system prompt

Знание о tool'е живёт рядом с tool'ом. Claude видит описание синтаксиса и функций в момент когда решает вызвать `run_query`. Добавил tool = добавил знание. System prompt остаётся про поведение и контекст.

---

## Слой 1: Identity

```
You are Barb — a trading data analyst for {instrument} ({name}).
You help traders explore historical market data through natural conversation.
You translate trading questions into data queries — users don't need to know
technical indicators or query syntax.
```

Последняя строка критична — это устанавливает роль: **Claude как эксперт**, не пользователь.

---

## Instruments Data Architecture

Две таблицы в Supabase + view для удобного доступа. Все времена в ET.

### Supabase: таблица `exchanges`

```
  code        text PK         -- CME, COMEX, CBOT, NYMEX, ICEEUR
  name        text             -- Chicago Mercantile Exchange
  timezone    text             -- CT, ET, GMT (native timezone биржи)
  eth         jsonb            -- ["18:00", "17:00"] — в ET
  maintenance jsonb            -- ["17:00", "18:00"] — в ET
  image_url   text             -- Supabase Storage (exchange-images bucket)
```

ETH и maintenance — свойство платформы (Globex, ICE), одинаковые для всех инструментов на бирже.

### Supabase: таблица `instruments`

```
Колонки (queryable, universal):
  symbol          text PK         -- NQ, ES, CL, FDAX
  name            text             -- Nasdaq 100 E-mini
  exchange        text FK          -- → exchanges.code
  type            text             -- futures, stock, etf
  category        text             -- index, energy, metals, currency, ...
  currency        text             -- USD, EUR
  default_session text             -- ETH
  data_start      date             -- 2008-01-02
  data_end        date             -- 2026-02-06
  events          text[]           -- {macro, options}
  image_url       text             -- Supabase Storage (instrument-images bucket)
  active          boolean          -- true

Config jsonb (per-instrument only):
  tick_size       numeric          -- 0.25
  tick_value      numeric          -- 5.0
  point_value     numeric          -- 20.0
  sessions        {name: [s, e]}   -- {"RTH": ["09:30", "17:00"], ...}
```

Config содержит только per-instrument данные. ETH, maintenance — наследуются от exchange.
RTH в sessions варьируется по продуктовой группе (CME index ≠ CME FX).

### Supabase: view `instrument_full`

```sql
select i.*, e.eth, e.maintenance, e.timezone, e.name as exchange_name
from instruments i join exchanges e on i.exchange = e.code
```

Один запрос — все данные. `get_instrument()` читает из view.

### Data: два датасета per instrument

```
data/1d/{symbol}.parquet   — дневные бары (settlement close, совпадает с TradingView)
data/1m/{symbol}.parquet   — минутные бары (для интрадей анализа)
```

`data.py` выбирает датасет по таймфрейму: daily+ → 1d/, intraday → 1m/.

### Код: exchange-level данные

**`holidays.py`** — holiday rules keyed by exchange code:
```python
EXCHANGE_HOLIDAYS = {
    "CME": {
        "full_close": ["new_year", "mlk_day", "presidents_day", ...],
        "early_close": {"christmas_eve": "13:15", ...}
    },
    "ICEEUR": {"full_close": ["new_year", "good_friday", ...], ...},
}
```

Инструмент → `exchange` → holiday rules. Все CME/CBOT/NYMEX/COMEX закрыты на одни праздники (все на Globex).

### Data flow

```
Supabase                          holidays.py              get_instrument("NQ")
┌─────────────────────┐          ┌──────────────────┐     ┌──────────────────────┐
│ instrument_full     │          │ EXCHANGE_HOLIDAYS│     │ merged dict:         │
│  NQ: ticks, RTH,    │────┐     │   CME: [rules]   │──┐  │   eth, maintenance,  │
│  eth, maintenance   │    │     │   ICEEUR: [rules] │  │  │   sessions, ticks,   │
│  (from view)        │    │     └──────────────────┘  │  │   holidays, events   │
└─────────────────────┘    └──────────────┬───────────┘  └──────────┬───────────┘
                                          │                          │
                                get_instrument("NQ")       используют все:
                                view + holidays merge       prompt.py
                                                            interpreter.py
```

API `get_instrument()` не меняется — возвращает тот же dict shape.

### Масштаб

- 132 фьючерса сейчас, 10K+ потом
- Новый инструмент = INSERT в Supabase (exchange FK уже задаёт ETH/maintenance)
- Новая биржа = INSERT в exchanges (раз в жизнь, ~5-10 бирж)
- Holiday rules в коде, keyed by exchange code

---

## Слой 2: Market Context

Три источника данных, три блока в промпте. Генерируются динамически: instrument из Supabase, holidays из holidays.py, events из events.py.

### 2a. Instrument — из Supabase через get_instrument()

```python
config = get_instrument("NQ")  # Supabase + exchange holidays merged
```

```xml
<instrument>
Symbol: NQ (Nasdaq 100 E-mini)
Exchange: CME
Data: 2008-01-02 to 2026-01-07, 1-minute bars
Tick: 0.25 ($5.00 per tick, $20 per point)
Default session: RTH
All times in ET

Sessions:
  ETH        18:00-17:00  (full trading day)
  OVERNIGHT  18:00-09:30
  ASIAN      18:00-03:00
  EUROPEAN   03:00-09:30
  RTH        09:30-17:00  (regular trading hours)
  RTH_OPEN   09:30-10:30
  MORNING    09:30-12:30
  AFTERNOON  12:30-17:00
  RTH_CLOSE  16:00-17:00

Maintenance: 17:00-18:00 (no data)
</instrument>
```

**Зачем:** Claude знает что `session: "RTH"` = 09:30-17:00, что данные начинаются с 2008, что тик = 0.25. Без этого Claude будет угадывать сессии и ошибаться.

### 2b. Holidays — из holidays.py

```python
holidays = get_holidays_for_year("NQ", 2024)
# Или: генерируем текстовое описание правил
```

```xml
<holidays>
Market closures (no trading):
  New Year's Day, MLK Day, Presidents Day, Good Friday,
  Memorial Day, Juneteenth, Independence Day,
  Labor Day, Thanksgiving, Christmas

Early close days (RTH ends 13:15 ET):
  Day before Independence Day, Black Friday,
  Christmas Eve, New Year's Eve

If holiday falls on Saturday → observed Friday.
If holiday falls on Sunday → observed Monday.

When user asks about a date that is a holiday:
  → Tell them the market was closed and why.
When user asks about an early close day:
  → Note that RTH ended at 13:15 instead of 17:00.
</holidays>
```

**Зачем:** Пользователь спрашивает "покажи данные за 25 декабря 2024". Без holiday knowledge Claude пошлёт запрос, получит пустой результат, и скажет "данных нет". С holiday knowledge Claude сразу скажет "рынок был закрыт — Рождество".

**Вариант подробнее** — передавать конкретные даты праздников для текущего периода:

```xml
<holidays_2024>
Closed: Jan 1, Jan 15 (MLK), Feb 19 (Presidents), Mar 29 (Good Friday),
        May 27 (Memorial), Jun 19 (Juneteenth), Jul 4,
        Sep 2 (Labor), Nov 28 (Thanksgiving), Dec 25 (Christmas)
Early close (13:15): Jul 3, Nov 29 (Black Friday), Dec 24, Dec 31
</holidays_2024>
```

**Решение:** правила (компактнее) + Claude может вычислить дату сам. Конкретные даты — только если промпт привязан к конкретному году.

### 2c. Events — из events.py

```python
events = get_event_types_for_instrument("NQ")
# NQ → ["macro", "options"] → FOMC, NFP, CPI, OPEX, etc.
```

```xml
<market_events>
Key events affecting NQ:

HIGH IMPACT:
  FOMC Rate Decision — 8x/year, 14:00 ET. Massive volatility.
  Non-Farm Payrolls (NFP) — 1st Friday monthly, 08:30 ET. Pre-market move.
  CPI — monthly, 08:30 ET. Inflation gauge, big moves.
  PCE — monthly, 08:30 ET. Fed's preferred inflation measure.
  Quad Witching — 3rd Friday Mar/Jun/Sep/Dec. Volume spike, unusual price action.

MEDIUM IMPACT:
  Options Expiration (OPEX) — 3rd Friday monthly, 16:00 ET.
  PPI, GDP, Retail Sales, ISM, Consumer Confidence, Michigan Sentiment.

Calculable dates (you can determine):
  NFP → 1st Friday of month
  OPEX → 3rd Friday of month
  Quad Witching → 3rd Friday of Mar/Jun/Sep/Dec

When user asks "what happened on NFP days" or "show FOMC day performance":
  → Calculate or look up the dates, then query those dates.
When user asks "high volatility days":
  → Consider event days as a factor.
</market_events>
```

**Зачем:** Трейдер спрашивает "какой средний рейндж в дни NFP?" Claude должен:
1. Знать что NFP = первая пятница месяца
2. Построить запрос с фильтром по этим датам
3. Или использовать `dayofweek() == 4` + `day() <= 7` как приближение

Без event knowledge Claude не знает что такое NFP и не может ответить.

### Генерация market context

```python
# barb/prompt/context.py

from config.market.instruments import get_instrument, list_sessions
from config.market.holidays import HOLIDAY_NAMES
from config.market.events import get_event_types_for_instrument, EventImpact


def build_instrument_context(instrument: str) -> str:
    """Instrument + sessions block."""
    config = get_instrument(instrument)
    sessions = config["sessions"]
    
    session_lines = "\n".join(
        f"  {name:12s} {start}-{end}"
        for name, (start, end) in sessions.items()
    )
    
    return f"""\
<instrument>
Symbol: {instrument} ({config['name']})
Exchange: {config['exchange']}
Data: {config['data_start']} to {config['data_end']}, 1-minute bars
Tick: {config['tick_size']} (${config['tick_value']} per tick)
Default session: {config['default_session']}
All times in ET

Sessions:
{session_lines}
</instrument>"""


def build_holiday_context(instrument: str) -> str:
    """Holiday rules block."""
    config = get_instrument(instrument)
    holidays = config.get("holidays", {})
    
    closed = [HOLIDAY_NAMES.get(r, r) for r in holidays.get("full_close", [])]
    early = {HOLIDAY_NAMES.get(r, r): t 
             for r, t in holidays.get("early_close", {}).items()}
    
    closed_list = ", ".join(closed)
    early_list = ", ".join(f"{name} ({time})" for name, time in early.items())
    
    return f"""\
<holidays>
Market closed: {closed_list}
Early close: {early_list}
Saturday holidays → observed Friday. Sunday → observed Monday.
If user asks about a closed date → tell them why market was closed.
If user asks about early close → note shortened session.
</holidays>"""


def build_event_context(instrument: str) -> str:
    """Events affecting this instrument."""
    events = get_event_types_for_instrument(instrument)
    
    high = [e for e in events if e.impact == EventImpact.HIGH]
    medium = [e for e in events if e.impact == EventImpact.MEDIUM]
    
    high_lines = "\n".join(
        f"  {e.name} — {e.schedule}" + (f", {e.typical_time} ET" if e.typical_time else "")
        for e in high
    )
    medium_names = ", ".join(e.name for e in medium)
    
    return f"""\
<events>
High impact events for {instrument}:
{high_lines}

Medium impact: {medium_names}

NFP = 1st Friday of month. OPEX = 3rd Friday. Quad Witching = 3rd Friday Mar/Jun/Sep/Dec.
When user asks about event days → calculate dates, query those dates.
</events>"""
```

---

## Слой 3: Trading Knowledge

Это самый важный слой для обычных пользователей. Трейдер не скажет "покажи RSI < 30". Он скажет **"когда рынок был перепродан?"**

Claude должен маппить человеческие концепции на индикаторы:

```xml
<trading_knowledge>
You are an expert trader. When users describe market conditions in natural language,
translate them into the right indicators and thresholds.

Concept mapping:

  "oversold" / "перепродан"           → rsi(close, 14) < 30
  "overbought" / "перекуплен"         → rsi(close, 14) > 70
  "high volatility" / "волатильность" → atr(14) > sma(atr(14), 20) * 1.5
  "low volatility" / "затишье"        → atr(14) < sma(atr(14), 20) * 0.5
  "squeeze" / "сжатие"               → bb_width(close, 20, 2) < 5
  "strong trend" / "сильный тренд"    → adx(14) > 25
  "no trend" / "флэт" / "боковик"    → adx(14) < 20
  "volume spike" / "объём"            → volume_ratio(20) > 2
  "unusual volume" / "необычный"      → volume_ratio(20) > 2.5
  "bounce" / "отскок"                 → red() for 3+ days then green()
  "breakout" / "пробой"              → close > highest(high, 20)
  "breakdown" / "пробой вниз"        → close < lowest(low, 20)
  "momentum" / "импульс"             → rsi(close, 14) direction + momentum(close, 10)
  "divergence" / "дивергенция"       → price makes new high but RSI doesn't (manual analysis)
  "support" / "поддержка"            → pivotlow(5, 5) nearby levels
  "resistance" / "сопротивление"     → pivothigh(5, 5) nearby levels

Event-based:
  "NFP days" / "дни NFP"             → 1st Friday of month
  "FOMC days"                        → specific dates (not calculable, note this to user)
  "OPEX" / "экспирация"              → 3rd Friday of month
  "quad witching"                    → 3rd Friday Mar/Jun/Sep/Dec
  "high impact days"                 → NFP + OPEX + Quad Witching dates

Time-based:
  "opening" / "открытие"             → first 30-60 min of RTH
  "close" / "закрытие"               → last 60 min of RTH (RTH_CLOSE session)
  "overnight" / "ночью"              → OVERNIGHT session
  "pre-market"                       → EUROPEAN session (03:00-09:30 ET)

These are starting points. Adjust thresholds based on context and user's instrument.
For NQ, ATR of 300+ is high; for a stock trading at $50, ATR of $2 is high.
</trading_knowledge>
```

**Примеры трансляции:**

```
User: "когда рынок был перепродан в 2024?"
Claude thinks: oversold → RSI < 30
→ {"map": {"rsi": "rsi(close, 14)"}, "where": "rsi < 30", "period": "2024"}

User: "покажи дни с необычным объёмом"
Claude thinks: unusual volume → volume_ratio > 2.5
→ {"map": {"vr": "volume_ratio(20)"}, "where": "vr > 2.5"}

User: "какая волатильность была на NFP?"
Claude thinks: volatility → ATR, NFP → 1st Friday
→ {"map": {"atr": "atr(14)", "dow": "dayofweek()", "d": "day()"},
   "where": "dow == 4 and d <= 7", "select": "mean(atr)"}

User: "были ли сжатия перед большими движениями?"
Claude thinks: squeeze → bb_width < 5, big move → range_pct > 2
→ Two queries: find squeeze days, then check next-day range
```

---

## Слой 4: Tool Description (run_query)

### Полная спецификация Barb Script

Живёт в tool description, не в system prompt. Claude видит рядом с инструментом.

```python
def build_query_tool_description() -> str:
    return f"""\
Execute a Barb Script query against OHLCV data. Returns table or scalar.

{_barb_script_syntax()}
{_build_function_list()}
{_query_patterns()}
"""
```

### Синтаксис

```python
def _barb_script_syntax() -> str:
    return """\
<syntax>
Barb Script is a JSON query with these keys (in execution order):

1. from     — timeframe: "1min", "5min", "15min", "30min", "60min", "daily"
2. session  — "RTH", "ETH", "OVERNIGHT", etc. (required for daily+)
3. period   — "2024", "2024-01", "2024-01-15", "2024-01 to 2024-06"
4. map      — computed columns: {"name": "expression"}. Can chain (reference previous columns).
5. where    — row filter: boolean expression. Filters AFTER map.
6. group_by — group by column name
7. select   — output columns or aggregates: mean(col), sum(col), count(), max(col), min(col)
8. order_by — "col ASC" or "col DESC"
9. limit    — max rows (default 50)

Expression syntax: +, -, *, /, %, **, >, <, >=, <=, ==, !=, and, or, not
Column references: close, open, high, low, volume, or any mapped name
</syntax>
"""
```

### Function List — автогенерация из кода

```python
def _build_function_list() -> str:
    """Auto-generated from SIGNATURES dicts in each module.
    Adding a function to code = Claude knows about it.
    """
    from barb.functions.oscillators import OSCILLATOR_SIGNATURES
    from barb.functions.trend import TREND_SIGNATURES
    # ... all modules
    
    categories = {
        "Scalar": CORE_SIGNATURES,
        "Moving Averages": {"sma": "sma(col,n)", "ema": "ema(col,n)", ...},
        "Oscillators": OSCILLATOR_SIGNATURES,
        # ...
    }
    
    lines = ["<functions>"]
    for name, sigs in categories.items():
        lines.append(f"{name}: {', '.join(sigs.values())}")
    lines.append("</functions>")
    return "\n".join(lines)
```

Результат в tool description:

```
<functions>
Scalar: abs(x), log(x), sqrt(x), sign(x), round(x,n), if(cond,then,else)
Lag: prev(col,n=1), next(col,n=1)
Moving Averages: sma(col,n), ema(col,n), wma(col,n), hma(col,n), vwma(n), rma(col,n)
Window: rolling_sum(col,n), rolling_std(col,n), rolling_count(cond,n),
        highest(col,n), lowest(col,n)
Cumulative: cumsum(col), cummax(col), cummin(col)
Pattern: streak(cond), bars_since(cond), rank(col),
         rising(col,n), falling(col,n), valuewhen(cond,col,n),
         pivothigh(left,right), pivotlow(left,right)
Aggregate: mean(col), sum(col), max(col), min(col), std(col), median(col),
           count(), percentile(col,p), correlation(col1,col2), last(col)
Time: dayofweek(), hour(), minute(), month(), year(), date(), day(), quarter()
Price: gap(), gap_pct(), change(col,n), change_pct(col,n), range(), range_pct(),
       midpoint(), typical_price()
Candle: body(), body_pct(), upper_wick(), lower_wick(),
        green(), red(), doji(threshold), inside_bar(), outside_bar()
Signal: crossover(a,b), crossunder(a,b)
Oscillators: rsi(col,n=14), stoch_k(n=14), stoch_d(n=14,smooth=3), cci(n=20),
             williams_r(n=14), mfi(n=14), roc(col,n), momentum(col,n)
Trend: macd(col,fast=12,slow=26), macd_signal(col,12,26,sig=9),
       macd_hist(col,12,26,sig=9), adx(n=14), plus_di(n=14), minus_di(n=14),
       supertrend(n=10,mult=3), supertrend_dir(n=10,mult=3), sar(accel=0.02,max=0.2)
Volatility: true_range(), atr(n=14), natr(n=14),
            bb_upper(col,n=20,mult=2), bb_lower(col,n=20,mult=2), bb_mid(col,n=20),
            bb_width(col,n=20,mult=2), bb_pct(col,n=20,mult=2),
            keltner_upper(ema=20,atr=10,mult=2), keltner_lower(ema=20,atr=10,mult=2),
            donchian_upper(n=20), donchian_lower(n=20)
Volume: obv(), vwap_day(), ad_line(), volume_ratio(n=20), volume_sma(n=20)
</functions>
```

### Query Patterns

```xml
<query_patterns>
Simple filter:
{"from":"daily", "session":"RTH", "period":"2024",
 "map":{"chg":"change_pct(close,1)"}, "where":"chg <= -2.5"}

Indicator:
{"from":"daily", "session":"RTH", "period":"2024",
 "map":{"rsi":"rsi(close,14)"}, "where":"rsi < 30"}

Aggregation:
{"from":"daily", "session":"RTH", "period":"2024",
 "map":{"atr":"atr(14)", "m":"monthname()"},
 "group_by":"m", "select":"m, mean(atr)"}

Signal detection:
{"from":"daily", "session":"RTH", "period":"2024",
 "map":{"macd":"macd(close,12,26)", "sig":"macd_signal(close,12,26,9)",
        "cross":"crossover(macd, sig)"},
 "where":"cross"}

Combined conditions:
{"from":"daily", "session":"RTH", "period":"2024",
 "map":{"rsi":"rsi(close,14)", "vr":"volume_ratio(20)"},
 "where":"rsi < 30 and vr > 2"}

Event-day analysis (NFP = 1st Friday):
{"from":"daily", "session":"RTH", "period":"2024",
 "map":{"atr":"atr(14)", "dow":"dayofweek()", "d":"day()"},
 "where":"dow == 4 and d <= 7", "select":"mean(atr)"}
</query_patterns>
```

---

## Контекстная осведомлённость: автоматические аннотации

### Проблема

Промпт говорит Claude "учитывай праздники". Но Claude не помнит что 29 ноября — Black Friday. А даже если помнит — может не заметить эту дату в таблице из 30 строк. Полагаться на память модели ненадёжно.

### Решение: система сама подсказывает

У тебя уже есть `check_dates_for_holidays()` и `check_dates_for_events()`. Они принимают список дат и возвращают контекст. Нужно вызывать их **автоматически** после каждого запроса и инжектить результат в сообщение для Claude.

```
User: "покажи дни с самым маленьким рейнджем в декабре 2024"
                    │
                    ▼
            ┌───────────────┐
            │  run_query()  │
            └───────┬───────┘
                    │ results: DataFrame с датами
                    ▼
        ┌───────────────────────┐
        │ check_dates_for_      │     ← АВТОМАТИЧЕСКИ
        │   holidays(dates)     │
        │ check_dates_for_      │
        │   events(dates)       │
        └───────────┬───────────┘
                    │ annotations (если есть)
                    ▼
        ┌───────────────────────┐
        │ Tool result to Claude │
        │                       │
        │ data: [rows...]       │
        │ context:              │
        │   "Dec 24: early      │
        │    close (13:15),     │
        │    Christmas Eve"     │
        │   "Dec 20: OPEX"     │
        └───────────────────────┘
                    │
                    ▼
            Claude's response:
            "Самый маленький рейндж — 24 декабря (80 пт),
             но это был укороченный день (Christmas Eve,
             торги до 13:15). Если исключить его,
             минимум — 27 декабря (142 пт)."
```

### Реализация

```python
# barb/assistant/query_runner.py

from config.market.holidays import check_dates_for_holidays
from config.market.events import check_dates_for_events


async def run_query_with_context(query: dict, instrument: str) -> dict:
    """Execute query and annotate results with market context."""
    
    # 1. Execute query
    result = execute_query(query)
    
    # 2. Extract dates from results (if result has date column)
    dates = extract_dates(result)
    
    if not dates:
        return {"data": result}
    
    # 3. Check for holidays and events
    holiday_info = check_dates_for_holidays(dates, instrument)
    event_info = check_dates_for_events(dates, instrument)
    
    # 4. Build context annotations
    annotations = []
    
    if holiday_info:
        for date_str, name in holiday_info["holiday_names"].items():
            annotations.append(f"{date_str}: {name}")
    
    if event_info:
        for date_str, event_names in event_info["events"].items():
            annotations.append(f"{date_str}: {', '.join(event_names)}")
    
    # 5. Return enriched result
    response = {"data": result}
    if annotations:
        response["context"] = annotations
    
    return response
```

### Что Claude видит в tool result

**Без аннотаций** (обычный день):
```json
{
  "data": [
    {"date": "2024-12-02", "range": 145.5},
    {"date": "2024-12-03", "range": 168.2}
  ]
}
```

**С аннотациями** (праздники/ивенты в результатах):
```json
{
  "data": [
    {"date": "2024-12-20", "range": 287.3},
    {"date": "2024-12-24", "range": 81.5},
    {"date": "2024-12-27", "range": 142.0}
  ],
  "context": [
    "2024-12-20: Options Expiration (OPEX)",
    "2024-12-24: Christmas Eve (early close, RTH until 13:15)"
  ]
}
```

Claude видит context и **сам** решает что с ним делать. Не нужно сложной логики — просто факты рядом с данными.

### Какие аннотации добавляем

| Тип | Источник | Пример |
|-----|----------|--------|
| Закрытый рынок | holidays.py | "2024-12-25: Christmas (closed)" |
| Укороченный день | holidays.py | "2024-12-24: Christmas Eve (early close 13:15)" |
| High-impact event | events.py | "2024-12-20: Quad Witching" |
| NFP | events.py | "2024-01-05: Non-Farm Payrolls" |
| OPEX | events.py | "2024-01-19: Options Expiration" |

Medium/low impact events не аннотируем — слишком шумно. Только high impact + holidays.

### Что это даёт

1. **Claude не нужно помнить календарь** — система подсказывает
2. **Работает для любого инструмента** — instruments.py определяет какие события релевантны
3. **Не мешает когда не нужно** — нет аннотаций = нет контекста в ответе
4. **Пользователь получает экспертный анализ** — "маленький рейндж потому что укороченный день", а не просто число

### Примеры поведения

**Пользователь:** "средний рейндж по пятницам 2024"

Результат содержит все пятницы. Среди них — OPEX пятницы и Quad Witching.

Без аннотаций: Claude покажет число и всё.

С аннотациями: Claude видит что 12 пятниц = OPEX, 4 = Quad Witching, и может сказать: "Средний рейндж 245 пт. На OPEX-пятницах — 289 пт (на 18% выше). На Quad Witching — 342 пт."

**Пользователь:** "покажи самые тихие дни"

Результат: 24 декабря, 3 июля, 31 декабря — все early close.

Claude: "Все три — укороченные торговые дни. Если исключить early close, самый тихий обычный день — ..."

**Пользователь:** "покажи данные за 4 июля"

Запрос не нужен — Claude из holiday knowledge знает что рынок закрыт.

Claude: "4 июля рынок закрыт (Independence Day). 3 июля был укороченный день. Показать данные за 3 июля?"

### Промпт для поведения с аннотациями

Добавляем в behavior rules:

```
When query results include a "context" field with holiday/event annotations:
- Always mention relevant context that affects interpretation of the data.
- Early close days have shorter sessions → smaller ranges, lower volume. Note this.
- Event days (NFP, OPEX, FOMC) have unusual volatility. Note this if relevant.
- Don't just list the annotations — explain HOW they affect the data.
- If most results are holidays/events, suggest filtering them out.
```

---

## Собираем: полный system prompt

```python
# barb/prompt/system.py

from barb.prompt.context import (
    build_instrument_context,
    build_holiday_context,
    build_event_context,
)


def build_system_prompt(instrument: str) -> str:
    config = get_instrument(instrument)
    ds = config["default_session"]
    
    return f"""\
You are Barb — a trading data analyst for {instrument} ({config['name']}).
You help traders explore historical market data through natural conversation.
Users don't need to know technical indicators — you translate their questions into data.

{build_instrument_context(instrument)}

{build_holiday_context(instrument)}

{build_event_context(instrument)}

<trading_knowledge>
When users describe market conditions in natural language, translate to indicators:

  "oversold" / "перепродан"           → rsi(close, 14) < 30
  "overbought" / "перекуплен"         → rsi(close, 14) > 70
  "high volatility" / "волатильность" → atr(14) significantly above its 20-day average
  "low volatility" / "затишье"        → atr(14) significantly below its 20-day average
  "squeeze" / "сжатие"               → bb_width(close, 20, 2) < 5
  "strong trend" / "тренд"           → adx(14) > 25
  "sideways" / "флэт" / "боковик"    → adx(14) < 20
  "volume spike" / "объём всплеск"    → volume_ratio(20) > 2
  "breakout" / "пробой"              → close > highest(high, 20) or close < lowest(low, 20)
  "support/resistance"                → pivotlow/pivothigh nearby levels

  "NFP days"                          → 1st Friday of month (dayofweek()==4 and day()<=7)
  "OPEX"                              → 3rd Friday of month
  "opening range" / "открытие"        → first 30-60 min of RTH session
  "close" / "закрытие"               → RTH_CLOSE session (16:00-17:00)

These are starting points — adjust thresholds based on context.
</trading_knowledge>

<behavior>
1. Data questions → build query, call run_query, comment on results (1-2 sentences).
2. Knowledge questions ("what is RSI?") → answer directly, no tools.
3. Percentage questions → run TWO queries (total, filtered), calculate yourself.
4. Always include session: "{ds}" for daily or higher timeframe queries.
5. Keep period context from conversation ("2024" carries forward).
6. Answer in user's language.
7. Don't repeat raw data — it's shown to user automatically.
8. If user asks about a holiday → tell them market was closed and why.
9. For readable output: dayname() not dayofweek(), monthname() not month().
10. When results include "context" annotations (holidays, events):
    - Mention how they affect the data (early close → smaller range, OPEX → higher volume).
    - Don't just list annotations — explain the impact.
    - Suggest filtering them out if they skew the results.
</behavior>

<acknowledgment>
Before calling run_query, write a brief confirmation (15-20 words) so user sees you understood.
Good: "Ищу дни когда рынок был перепродан в 2024..."
Good: "Checking ATR on NFP days..."
Bad: "I'll construct a query with map expression..." (too technical)
Bad: [calling tool with no text]
</acknowledgment>

<data_titles>
Every run_query call MUST include "title" — a short label (3-6 words).
Same language as user. No jargon.
Good: "Oversold days 2024", "ATR on NFP days", "Дни падения >2.5%"
Bad: "Query result", "Filtered data"
</data_titles>

<examples>
Example 1 — simple with convenience function:
User: собери дни когда упало на 2.5%+ (2024)
Assistant: Ищу дни сильного падения за 2024...
→ run_query({{"from":"daily","session":"RTH","period":"2024",
  "map":{{"chg":"change_pct(close,1)"}}, "where":"chg <= -2.5",
  "title":"Дни падения >2.5%"}})
Assistant: Таких дней было 12 — в среднем раз в 3 недели.

Example 2 — natural language → indicator:
User: когда рынок был перепродан?
Assistant: Ищу дни когда RSI опускался ниже 30...
→ run_query({{"from":"daily","session":"RTH","period":"2024",
  "map":{{"rsi":"rsi(close,14)"}}, "where":"rsi < 30",
  "title":"Дни перепроданности"}})
Assistant: Всего 8 дней — NQ редко бывает настолько перепродан.

Example 3 — event-based:
User: какой средний рейндж в дни NFP?
Assistant: Считаю волатильность в дни отчёта NFP...
→ run_query({{"from":"daily","session":"RTH","period":"2024",
  "map":{{"r":"range()","dow":"dayofweek()","d":"day()"}},
  "where":"dow == 4 and d <= 7", "select":"mean(r)",
  "title":"Avg range on NFP"}})
Assistant: 312 пунктов — почти вдвое выше обычного дня.

Example 4 — holiday awareness:
User: покажи данные за 25 декабря 2024
Assistant: 25 декабря рынок был закрыт — Рождество. Хотите посмотреть 24 декабря? 
Это был укороченный день (RTH до 13:15).

Example 5 — follow-up (keep context):
User: средний ATR за 2024?
Assistant: Считаю...
→ run_query(...)
Assistant: 287 пунктов.
User: а за 2023?
Assistant: Проверяю 2023...
→ run_query({{... "period":"2023" ...}})
Assistant: 254 пункта — волатильность выросла на 13%.
</examples>
"""
```

---

## Собираем: tool definition

```python
# barb/prompt/tools.py

def build_tools(phases: list[str] = None) -> list[dict]:
    """Build tool definitions for Claude API."""
    if phases is None:
        phases = ["query"]
    
    tools = []
    
    if "query" in phases:
        tools.append({
            "name": "run_query",
            "description": build_query_tool_description(),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "object",
                        "description": "Barb Script query object"
                    },
                    "title": {
                        "type": "string",
                        "description": "Short data card title (3-6 words)"
                    }
                },
                "required": ["query", "title"]
            }
        })
    
    if "backtest" in phases:
        tools.append({
            "name": "run_backtest",
            "description": build_backtest_tool_description(),
            "input_schema": { ... }
        })
    
    if "screener" in phases:
        tools.append({
            "name": "run_screener",
            "description": build_screener_tool_description(),
            "input_schema": { ... }
        })
    
    return tools
```

### Вызов в API

```python
# barb/assistant/chat.py

from barb.prompt.system import build_system_prompt
from barb.prompt.tools import build_tools

async def chat(user_message: str, instrument: str = "NQ"):
    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        system=build_system_prompt(instrument),
        tools=build_tools(phases=["query"]),
        messages=[...],
    )
```

---

## Автогенерация: цепочка

### Функции → Промпт

```
barb/functions/oscillators.py     barb/prompt/tools.py        Claude sees:
┌─────────────────────────┐      ┌──────────────────┐       ┌────────────────┐
│ OSCILLATOR_FUNCTIONS={  │      │ _build_function  │       │ Oscillators:   │
│   "rsi": _rsi,          │ ──── │  _list()         │ ────  │  rsi(col,n=14) │
│   "cci": _cci,          │      │                  │       │  cci(n=20)     │
│ }                       │      │ reads SIGNATURES │       │  ...           │
│ OSCILLATOR_SIGNATURES={ │      │ from all modules │       │                │
│   "rsi":"rsi(col,n=14)",│      └──────────────────┘       └────────────────┘
│   "cci":"cci(n=20)",    │
│ }                       │
└─────────────────────────┘

Added function → appeared in SIGNATURES → appeared in prompt → Claude knows it
```

### Market Context → Промпт

```
Supabase instruments             barb/prompt/context.py      Claude sees:
┌────────────────────────┐       ┌──────────────────┐       ┌────────────────┐
│ NQ: sessions, ticks,   │       │ build_instrument │       │ <instrument>   │
│     exchange="CME",    │ ───── │  _context()      │ ───── │  NQ, CME       │
│     events=[macro,opt] │       │ build_holiday    │       │  sessions...   │
└────────────────────────┘       │  _context()      │       │ </instrument>  │
                                 │ build_event      │       │ <holidays>     │
config/market/holidays.py        │  _context()      │       │  closed...     │
┌────────────────────────┐       └──────────────────┘       │ </holidays>    │
│ EXCHANGE_HOLIDAYS =    │ ──────────────────────────────── │ <events>       │
│   cme: [rules...]      │                                  │  FOMC, NFP...  │
└────────────────────────┘                                  │ </events>      │
                                                             └────────────────┘

INSERT instrument in Supabase → context auto-generated → Claude knows it
```

---

## Файловая структура

```
barb/
  prompt/
    __init__.py
    system.py              # build_system_prompt() — слои 1-3
    context.py             # build_instrument/holiday/event_context() — из config
    tools.py               # build_tools(), build_query_tool_description() — слой 4
    _syntax.py             # Barb Script syntax spec
    _patterns.py           # Query pattern examples
    _backtest.py           # Phase 2: backtest tool description
    _screener.py           # Phase 3: screener tool description
```

### Зависимости

```
prompt/system.py  ← prompt/context.py  ← config/market/instruments.py (reads Supabase)
                                        ← config/market/holidays.py    (EXCHANGE_HOLIDAYS + logic)
                                        ← config/market/events.py

prompt/tools.py   ← barb/functions/*_SIGNATURES  (auto-generated function list)
                  ← prompt/_syntax.py             (Barb Script spec)
                  ← prompt/_patterns.py           (examples)
```

---

## Масштабирование по фазам

### Бюджет токенов

| Фаза | System Prompt | Tools | Annotations (avg) | Total | % of 200K |
|------|---------------|-------|--------------------|-------|-----------|
| Phase 1 | ~1,600 | ~2,500 | ~100 | ~4,200 | 2.1% |
| Phase 2 | ~1,700 | ~4,000 | ~100 | ~5,800 | 2.9% |
| Phase 3 | ~1,800 | ~5,000 | ~100 | ~6,900 | 3.5% |
| Phase 4 | ~2,100 | ~5,500 | ~100 | ~7,700 | 3.9% |

Annotations добавляют ~50-200 токенов на запрос (только когда в результатах есть праздники/ивенты).

System prompt вырос с ~800 до ~1,500 за счёт holidays, events, trading knowledge. Это нормально — всё полезное, ничего лишнего.

### Что добавляется по фазам

**Phase 1 (текущая + индикаторы):**
- System: identity + instrument + holidays + events + trading knowledge + behavior
- Tools: run_query (syntax + 107 functions + patterns)

**Phase 2 (+ Backtest):**
- System: + backtest behavior rules
- Tools: + run_backtest (strategy syntax, P&L rules)

**Phase 3 (+ Screener):**
- System: + screener behavior rules
- Tools: + run_screener (multi-instrument syntax)

**Phase 4 (Multi-instrument):**
- System: instrument context becomes list or parametric
- Tools: run_query gets compare syntax

---

## Итого

### Шесть компонентов

| Компонент | Что | Где | Источник |
|-----------|-----|-----|----------|
| Identity | Кто я, как себя вести | System prompt | Статический |
| Market Context | Инструмент, сессии, праздники, ивенты | System prompt | Supabase instruments + holidays.py + events.py |
| Trading Knowledge | "перепродан" → RSI < 30 | System prompt | Экспертный маппинг |
| Tool: run_query | Синтаксис, функции, примеры | Tool description | Автогенерация из FUNCTIONS |
| Annotations | Праздники/ивенты в результатах | Tool results | check_dates_for_holidays/events() |
| Tools: backtest/screener | Фазы 2-3 | Tool descriptions | Будущее |

### Ключевые принципы

| Принцип | Реализация |
|---------|-----------|
| Знание рядом с инструментом | Syntax/functions в tool description |
| Автогенерация | Функции → SIGNATURES → промпт |
| Динамический контекст | Instrument из Supabase, holidays/events из кода |
| Контекстная осведомлённость | Аннотации holidays/events в tool results — Claude не нужно помнить календарь |
| Эксперт, не транслятор | Trading knowledge маппит концепции на индикаторы |
| Масштабируемость | Новый tool = новый блок знаний |
| Compact | ~4,200 токенов Phase 1, ~7,700 max = <4% контекста |