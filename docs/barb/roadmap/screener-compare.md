# Screener & Compare

Скрининг рынка и сравнение инструментов. Данные исторические, обновляются ежедневно (до вчерашнего close).

---

## Зачем

### Screener

Без скринера Barb — инструмент для **одного** тикера. С скринером — инструмент для **всего рынка**.

```
Без скринера:                          С скринером:
"Какой RSI у NQ?"                      "Какие акции перепроданы?"
→ один ответ                           → таблица из 15 акций
→ закрыл, ушёл                         → "расскажи про NVDA"
                                       → "протестируй стратегию на них"
                                       → ежедневная привычка
```

Скринер создаёт **daily workflow**: трейдер открывает Barb утром, спрашивает "что вчера было интересного", получает список, копает глубже по каждому тикеру. Это retention.

### Compare

Трейдеры постоянно сравнивают. NQ vs ES — кто волатильнее? AAPL vs MSFT — кто сильнее? BTC vs ETH — корреляция?

Без compare каждый инструмент — остров. С compare Barb видит **связи** и может дать рекомендации: "NQ в 1.5 раза волатильнее ES, но и рейнджи больше — больше потенциал для дейтрейдинга."

---

## User Experience

### Screener

```
User: "Какие акции из S&P 500 вчера закрылись с RSI ниже 30?"

Barb: Ищу перепроданные акции в S&P 500...

[Screener Results Card]
Found: 7 of 503 instruments

| Symbol | Close  | RSI   | Change % |
|--------|--------|-------|----------|
| INTC   | 24.31  | 18.7  | -4.2%    |
| PFE    | 26.85  | 22.1  | -2.8%    |
| BA     | 178.40 | 24.5  | -3.1%    |
| NKE    | 71.20  | 26.3  | -1.9%    |
| DIS    | 89.15  | 27.8  | -2.2%    |
| CVS    | 52.40  | 28.9  | -1.5%    |
| PYPL   | 63.70  | 29.4  | -1.1%    |

Barb: 7 акций с RSI < 30. INTC самая перепроданная — RSI 18.7 после
падения на 4.2%. Хотите посмотреть подробнее по какой-нибудь из них?
```

### Compare

```
User: "Сравни волатильность NQ и ES за 2024"

Barb: Сравниваю NQ и ES...

[Compare Results Card]
| Metric         | NQ     | ES     |
|----------------|--------|--------|
| Avg Range      | 312 pt | 58 pt  |
| Avg Range %    | 1.82%  | 1.24%  |
| Avg ATR(14)    | 287 pt | 52 pt  |
| Max Daily Move | 4.8%   | 3.2%   |
| Trading Days   | 251    | 251    |

Barb: NQ на 47% волатильнее ES по средней рейнджу. 
Максимальное дневное движение NQ — 4.8% против 3.2% у ES.
```

### Correlation

```
User: "Как коррелируют AAPL и SPY?"

Barb: Считаю корреляцию...

Correlation: 0.87 (daily close, 2024)
[Scatter plot: AAPL daily return vs SPY daily return]

Barb: Высокая корреляция 0.87 — AAPL движется в основном 
вместе с рынком, но с бо́льшим размахом.
```

---

## Архитектура

### Общий принцип

Скринер и Compare переиспользуют **тот же** query engine. Не нужен новый парсер, новые функции, новый пайплайн. Разница только в том **сколько раз** вызывается execute:

```
run_query   → execute(NQ, query)              → 1 DataFrame
run_screen  → execute(AAPL, query)            → N DataFrames → merge → 1 таблица
              execute(NVDA, query)
              execute(TSLA, query)
              ...
run_compare → execute(NQ, query)              → 2-10 DataFrames → compare → 1 таблица
              execute(ES, query)
```

### Файловая структура

```
barb/
  screener/
    __init__.py
    engine.py          # Screen loop: iterate universe, collect results
    universe.py        # Universe definitions and resolution
    cache.py           # Daily bars cache for performance

  compare/
    __init__.py
    engine.py          # Compare loop: run query on each, merge results
    metrics.py         # Correlation, relative strength, spread

assistant/
  tools/
    screener.py        # LLM tool wrapper for run_screen
    compare.py         # LLM tool wrapper for run_compare
```

Тот же принцип: `barb/screener/` и `barb/compare/` — чистый Python. `assistant/tools/` — тонкие обёртки для Claude.

---

## Screener

### Universe

Universe — набор инструментов для скрининга. Предопределённые + custom:

```python
@dataclass
class Universe:
    id: str                     # "sp500", "futures", "crypto"
    name: str                   # "S&P 500", "US Futures", "Crypto Top 50"
    symbols: list[str]          # ["AAPL", "MSFT", "GOOGL", ...]
    data_source: str            # как загружать данные
```

#### Предопределённые universes

```python
UNIVERSES = {
    # Индексные
    "sp500":      Universe("sp500", "S&P 500", [...503 symbols...]),
    "nasdaq100":  Universe("nasdaq100", "Nasdaq 100", [...100 symbols...]),
    "dow30":      Universe("dow30", "Dow Jones 30", [...30 symbols...]),
    
    # По классам активов
    "futures":    Universe("futures", "US Futures", 
                          ["NQ", "ES", "YM", "RTY", "CL", "GC", "SI", "ZB", "ZN", "6E"]),
    "crypto":     Universe("crypto", "Crypto Top 20",
                          ["BTC", "ETH", "SOL", "BNB", "XRP", ...]),
    
    # Секторы
    "tech":       Universe("tech", "Technology", [...]),
    "finance":    Universe("finance", "Financials", [...]),
    "energy":     Universe("energy", "Energy", [...]),
    "healthcare": Universe("healthcare", "Healthcare", [...]),
    
    # Популярные
    "mag7":       Universe("mag7", "Magnificent 7",
                          ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]),
}
```

#### Custom universe

Пользователь может указать список тикеров:

```json
"universe": ["AAPL", "MSFT", "GOOGL", "AMZN"]
```

Claude определяет что это: название universe или список тикеров.

#### Resolution

```python
def resolve_universe(universe: str | list[str]) -> list[str]:
    """Resolve universe to list of symbols."""
    if isinstance(universe, list):
        return universe  # custom list
    
    if universe in UNIVERSES:
        return UNIVERSES[universe].symbols
    
    raise ValueError(f"Unknown universe: {universe}")
```

### Tool Schema

```python
SCREENER_TOOL = {
    "name": "run_screen",
    "description": """Screen multiple instruments using Barb Script conditions.

Runs the same query across all instruments in a universe. Returns a table
with one row per instrument that matches the conditions.

Uses the same expressions and functions as run_query.
Data is through yesterday's close (updated daily).

Available universes: sp500, nasdaq100, dow30, futures, crypto,
mag7, tech, finance, energy, healthcare.
Or pass a list of symbols: ["AAPL", "MSFT", "GOOGL"]

The result always includes a 'symbol' column. Use 'select' to choose
which metrics to show. Without 'where', returns all instruments with
computed metrics (useful for ranking).
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "universe": {
                "description": "Universe name or list of symbols",
                "oneOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}}
                ]
            },
            "query": {
                "type": "object",
                "description": "Barb Script query (same as run_query, without 'from' — always daily)"
            },
            "title": {
                "type": "string",
                "description": "Short data card title (3-6 words)"
            }
        },
        "required": ["universe", "query", "title"]
    }
}
```

### Engine

```python
async def run_screen(
    universe: str | list[str],
    query: dict,
    instrument_configs: dict,
) -> ScreenResult:
    """Screen instruments in universe.
    
    1. Resolve universe to symbol list
    2. For each symbol: load data, execute query, extract last row
    3. Collect results into single DataFrame with 'symbol' column
    4. Apply where/order_by/limit on merged result
    """
```

#### Pipeline

```
Universe ("sp500")
    ↓
1. resolve_universe()          → ["AAPL", "MSFT", "GOOGL", ...]
    ↓
2. parallel for each symbol:
   a. load_daily_bars(symbol)  → DataFrame (from cache)
   b. evaluate map expressions → computed columns
   c. extract snapshot         → last row values (yesterday's close)
    ↓
3. merge snapshots             → single DataFrame with 'symbol' column
    ↓
4. apply where                 → filter instruments
    ↓
5. apply order_by              → sort
    ↓
6. apply limit                 → top N
    ↓
ScreenResult
```

#### Snapshot — что извлекаем

Для скринера нужны значения **на последний бар** (вчерашний close). Не вся история, а снимок:

```python
def extract_snapshot(df: pd.DataFrame, symbol: str) -> dict:
    """Extract last-row values for screener output."""
    last = df.iloc[-1]
    snapshot = {"symbol": symbol}
    
    for col in df.columns:
        if col not in ("date", "datetime"):  # skip index-like columns
            snapshot[col] = last[col]
    
    return snapshot
```

Но некоторые запросы требуют **агрегатов** по всей истории, не только last row:

```
"Какие акции выросли больше всего за 2024?"
→ нужен cumulative return, не last row
```

Решение: если `select` содержит агрегатные функции (mean, sum, count, max, min), применять их ко всему периоду. Если нет — брать last row.

```python
def extract_result(df: pd.DataFrame, symbol: str, select: list[str]) -> dict:
    """Extract screener result — snapshot or aggregate depending on select."""
    has_aggregates = any(is_aggregate(s) for s in select)
    
    if has_aggregates:
        # Aggregate over entire period
        result = {"symbol": symbol}
        for expr in select:
            result[expr] = evaluate_aggregate(df, expr)
        return result
    else:
        # Snapshot: last row values
        return extract_snapshot(df, symbol)
```

### Производительность

**Проблема:** 500 инструментов × загрузка + вычисление = может быть медленно.

**Решения:**

#### 1. Daily Bars Cache

Не читать минутные данные и ресемплить каждый раз. Хранить предрассчитанные daily bars:

```python
# barb/screener/cache.py

DAILY_CACHE_DIR = "data/daily_cache/"

def get_daily_bars(symbol: str) -> pd.DataFrame:
    """Load pre-computed daily bars from cache."""
    path = f"{DAILY_CACHE_DIR}/{symbol}.parquet"
    return pd.read_parquet(path)

def rebuild_cache(symbols: list[str]):
    """Nightly job: resample minute data to daily, save as parquet."""
    for symbol in symbols:
        df = load_minute_data(symbol)
        daily = resample_to_daily(df, session="RTH")
        daily.to_parquet(f"{DAILY_CACHE_DIR}/{symbol}.parquet")
```

Daily cache = мгновенная загрузка. 500 parquet файлов по ~50KB = 25MB total.

#### 2. Параллельное выполнение

```python
import asyncio

async def run_screen(universe, query):
    symbols = resolve_universe(universe)
    
    # Parallel execution
    tasks = [screen_one(symbol, query) for symbol in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out errors
    valid = [r for r in results if not isinstance(r, Exception)]
    
    return merge_results(valid)
```

#### 3. Streaming прогресс

500 инструментов — пользователь ждёт. Показываем прогресс:

```
event: screen_progress
data: {"processed": 150, "total": 503, "matches": 7}

event: screen_progress
data: {"processed": 300, "total": 503, "matches": 12}

event: screen_progress
data: {"processed": 503, "total": 503, "matches": 15}

event: data_block
data: {"type": "screen", "results": [...], "universe": "sp500", "total_scanned": 503}
```

#### Ожидаемые цифры

```
Daily cache read:     ~5ms per symbol
Expression eval:      ~10ms per symbol (RSI + volume_ratio)
──────────────────────────────────────
500 symbols sequential: ~7.5 sec
500 symbols parallel (10 workers): ~1 sec
30 symbols (dow30): ~150ms
7 symbols (mag7): ~50ms
```

### Result

```python
@dataclass
class ScreenResult:
    matches: list[dict]         # rows matching where condition
    total_scanned: int          # how many instruments checked
    universe: str               # which universe was scanned
    query_summary: str          # human-readable filter description
```

### Примеры

#### Oversold stocks

```
User: "Какие акции из S&P 500 перепроданы?"

Claude thinks: oversold → RSI < 30

→ run_screen({
    universe: "sp500",
    query: {
      "session": "RTH",
      "map": {"rsi": "rsi(close, 14)", "chg": "change_pct(close, 1)"},
      "where": "rsi < 30",
      "select": "close, rsi, chg",
      "order_by": "rsi ASC",
      "limit": 20
    },
    title: "Перепроданные S&P 500"
  })
```

#### Volume spike

```
User: "Где вчера был необычный объём? Фьючерсы."

→ run_screen({
    universe: "futures",
    query: {
      "session": "RTH",
      "map": {"vr": "volume_ratio(20)"},
      "where": "vr > 2",
      "select": "close, volume, vr",
      "order_by": "vr DESC"
    },
    title: "Volume spikes futures"
  })
```

#### Best performers (no filter — ranking)

```
User: "Какие акции из Magnificent 7 выросли больше всего за 2024?"

→ run_screen({
    universe: "mag7",
    query: {
      "session": "RTH",
      "period": "2024",
      "map": {"ret": "change_pct(close, 1)"},
      "select": "sum(ret)",
      "order_by": "sum(ret) DESC"
    },
    title: "Mag 7 returns 2024"
  })
```

#### Breakout candidates

```
User: "Какие акции из Nasdaq 100 вчера пробили 20-дневный максимум?"

→ run_screen({
    universe: "nasdaq100",
    query: {
      "session": "RTH",
      "map": {"hi20": "highest(high, 20)", "breakout": "close > hi20"},
      "where": "breakout",
      "select": "close, hi20",
      "order_by": "close DESC",
      "limit": 20
    },
    title: "Breakouts Nasdaq 100"
  })
```

#### Squeeze detection

```
User: "Где сейчас Bollinger squeeze?"

→ run_screen({
    universe: "sp500",
    query: {
      "session": "RTH",
      "map": {"bw": "bb_width(close, 20, 2)"},
      "where": "bw < 3",
      "select": "close, bw",
      "order_by": "bw ASC",
      "limit": 20
    },
    title: "Bollinger squeeze S&P 500"
  })
```

---

## Compare

### Два режима

**Metrics compare** — один и тот же расчёт по нескольким инструментам, таблица рядом:

```
"Сравни волатильность NQ, ES и YM"
→ таблица: symbol | avg_range | avg_atr | max_move
```

**Correlation** — как два инструмента связаны:

```
"Корреляция AAPL и SPY за 2024"
→ число: 0.87 + scatter plot
```

### Tool Schema

```python
COMPARE_TOOL = {
    "name": "run_compare",
    "description": """Compare metrics across 2-10 instruments.

Runs the same query on each instrument and shows results side-by-side.
Uses the same expressions and functions as run_query.

Two modes:
1. Metrics: compare aggregated values (mean, max, etc.) across instruments
2. Correlation: calculate price correlation between two instruments

For metrics, 'select' must contain aggregate functions.
For correlation, use compare_mode: "correlation" with exactly 2 instruments.
""",
    "input_schema": {
        "type": "object",
        "properties": {
            "instruments": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 10,
                "description": "List of symbols to compare"
            },
            "query": {
                "type": "object",
                "description": "Barb Script query (applied to each instrument)"
            },
            "compare_mode": {
                "type": "string",
                "enum": ["metrics", "correlation"],
                "description": "metrics (default): compare aggregated values. correlation: price correlation."
            },
            "title": {
                "type": "string",
                "description": "Short data card title (3-6 words)"
            }
        },
        "required": ["instruments", "query", "title"]
    }
}
```

### Engine

```python
async def run_compare(
    instruments: list[str],
    query: dict,
    compare_mode: str = "metrics",
) -> CompareResult:
    """Compare instruments.
    
    Metrics mode:
      1. Run query on each instrument
      2. Evaluate aggregate expressions
      3. Return table: symbol | metric1 | metric2 | ...
    
    Correlation mode:
      1. Run query on both instruments
      2. Align dates (inner join)
      3. Calculate correlation
      4. Return correlation + aligned series for scatter plot
    """
```

#### Metrics Pipeline

```
Instruments ["NQ", "ES", "YM"]
    ↓
1. for each instrument:
   a. load_daily_bars(symbol)
   b. apply session, period filters
   c. evaluate map expressions
   d. evaluate aggregate select → single row of metrics
    ↓
2. merge into comparison table
    ↓
CompareResult(mode="metrics")

Result:
| symbol | mean_range_pct | mean_atr | max_daily_move |
|--------|---------------|----------|----------------|
| NQ     | 1.82          | 287      | 4.8%           |
| ES     | 1.24          | 52       | 3.2%           |
| YM     | 1.15          | 401      | 2.9%           |
```

#### Correlation Pipeline

```
Instruments ["AAPL", "SPY"]
    ↓
1. load daily bars for both
2. apply session, period filters
3. evaluate map (e.g., change_pct)
4. align on date (inner join — only days both traded)
5. calculate correlation
6. prepare scatter plot data
    ↓
CompareResult(mode="correlation")

Result:
  correlation: 0.87
  n_days: 251
  scatter: [{x: 0.5, y: 0.3}, {x: -1.2, y: -0.8}, ...]
```

#### Alignment — важная деталь

Разные инструменты торгуются в разные дни:
- Акции не торгуются на stock market holidays
- Фьючерсы торгуются, когда акции нет (и наоборот)
- Крипта торгуется 24/7

Для корреляции нужны **совпадающие даты**:

```python
def align_series(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    on: str = "date",
) -> tuple[pd.Series, pd.Series]:
    """Align two series on common dates."""
    merged = df_a.merge(df_b, on=on, how="inner", suffixes=("_a", "_b"))
    return merged["close_a"], merged["close_b"]
```

### Result

```python
@dataclass
class CompareResult:
    mode: str                           # "metrics" | "correlation"
    
    # Metrics mode
    rows: list[dict] | None             # symbol → metric values
    
    # Correlation mode
    correlation: float | None           # Pearson correlation
    n_days: int | None                  # common trading days
    scatter_data: list[dict] | None     # [{x, y}, ...] for scatter plot
    
    # Metadata
    instruments: list[str]
    period: str | None
```

### Примеры

#### Volatility comparison

```
User: "Какой фьючерс самый волатильный?"

→ run_compare({
    instruments: ["NQ", "ES", "YM", "RTY", "CL", "GC"],
    query: {
      "session": "RTH",
      "period": "2024",
      "map": {"r": "range_pct()", "atr": "natr(14)"},
      "select": "mean(r), mean(atr), max(r)"
    },
    compare_mode: "metrics",
    title: "Volatility comparison futures"
  })
```

#### Correlation

```
User: "Как коррелируют AAPL и SPY?"

→ run_compare({
    instruments: ["AAPL", "SPY"],
    query: {
      "session": "RTH",
      "period": "2024",
      "map": {"ret": "change_pct(close, 1)"}
    },
    compare_mode: "correlation",
    title: "AAPL vs SPY correlation"
  })
```

#### Sector strength

```
User: "Сравни Magnificent 7 — кто лучше перформил в 2024?"

→ run_compare({
    instruments: ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    query: {
      "session": "RTH",
      "period": "2024",
      "map": {"ret": "change_pct(close, 1)"},
      "select": "sum(ret), max(ret), min(ret), count()"
    },
    compare_mode: "metrics",
    title: "Mag 7 performance 2024"
  })
```

#### Gap behavior across instruments

```
User: "Где гэпы закрываются чаще — NQ или ES?"

→ run_compare({
    instruments: ["NQ", "ES"],
    query: {
      "session": "RTH",
      "period": "2024",
      "map": {
        "g": "gap()",
        "has_gap": "abs(g) > 10",
        "filled": "if(g > 0, low <= prev(close), high >= prev(close))"
      },
      "where": "has_gap",
      "select": "count(), mean(if(filled, 1, 0))"
    },
    compare_mode: "metrics",
    title: "Gap fill rate NQ vs ES"
  })
```

#### Rolling correlation

```
User: "Как менялась корреляция BTC и NASDAQ за последние 2 года?"

Этот запрос сложнее — нужна корреляция по окнам.
Claude разбивает на периоды и делает несколько compare вызовов,
или использует run_query с ручным расчётом rolling correlation.
```

---

## Frontend Display

### Screener Results Card

```
┌────────────────────────────────────────────────────┐
│  Перепроданные S&P 500                             │
│  7 of 503 instruments match                       │
├────────────────────────────────────────────────────┤
│  Symbol  Close    RSI    Change %                  │
│  INTC    24.31    18.7   -4.2%                     │
│  PFE     26.85    22.1   -2.8%                     │
│  BA      178.40   24.5   -3.1%                     │
│  NKE     71.20    26.3   -1.9%                     │
│  DIS     89.15    27.8   -2.2%                     │
│  CVS     52.40    28.9   -1.5%                     │
│  PYPL    63.70    29.4   -1.1%                     │
├────────────────────────────────────────────────────┤
│  Scanned 503 instruments in 1.2s                   │
└────────────────────────────────────────────────────┘
```

Кликабельные символы — клик на "INTC" переключает контекст на этот инструмент, можно продолжать разговор про него.

### Compare Results Card

```
┌────────────────────────────────────────────────────┐
│  Volatility comparison futures (2024)              │
├────────────────────────────────────────────────────┤
│  Symbol  Avg Range %  Avg ATR  Max Move            │
│  NQ      1.82         287      4.8%                │
│  CL      1.65         1.82     6.2%                │
│  RTY     1.58         33       3.9%                │
│  ES      1.24         52       3.2%                │
│  GC      1.10         28       2.8%                │
│  YM      1.15         401      2.9%                │
├────────────────────────────────────────────────────┤
│  [Bar chart: Avg Range % by instrument]            │
└────────────────────────────────────────────────────┘
```

### Correlation Card

```
┌────────────────────────────────────────────────────┐
│  AAPL vs SPY correlation (2024)                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  Correlation: 0.87                                 │
│  Common trading days: 251                          │
│                                                    │
│  [Scatter plot: AAPL return vs SPY return]          │
│           •  •                                     │
│        •  • •• •                                   │
│      •  •••••• •  •                                │
│    ──•──••••••••──•──                              │
│      •  •••••••  •                                 │
│        •  •• •                                     │
│           •                                        │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## SSE Events

### Screener

```
event: tool_start
data: {"tool_name": "run_screen", "input": {...}}

event: screen_progress
data: {"processed": 100, "total": 503, "matches": 3}

event: screen_progress
data: {"processed": 300, "total": 503, "matches": 5}

event: data_block
data: {"type": "screen", "results": [...], "total_scanned": 503, "universe": "sp500"}

event: tool_end
data: {"tool_name": "run_screen", "duration_ms": 1200, "error": null}
```

Frontend показывает progress bar во время сканирования.

### Compare

```
event: tool_start
data: {"tool_name": "run_compare", "input": {...}}

event: data_block
data: {"type": "compare", "mode": "metrics", "rows": [...]}
// or
data: {"type": "compare", "mode": "correlation", "correlation": 0.87, "scatter": [...]}

event: tool_end
data: {"tool_name": "run_compare", "duration_ms": 350, "error": null}
```

Compare быстрый (2-10 инструментов), progress bar не нужен.

---

## Prompt Integration

### System prompt additions

```xml
<behavior>
...existing rules...
11. For screening questions ("what stocks are...", "find instruments where...") → use run_screen.
12. For comparison questions ("compare X and Y", "which is more volatile") → use run_compare.
13. For correlation questions → use run_compare with compare_mode: "correlation".
14. When user says "switch to AAPL" after screener results → change instrument context.
15. Screener data is through yesterday's close — note this if user expects real-time.
</behavior>
```

### Trading Knowledge additions

```xml
<trading_knowledge>
...existing concept mappings...

Screener patterns:
  "что перепроданы" / "oversold stocks"     → run_screen, rsi < 30
  "необычный объём" / "volume spikes"       → run_screen, volume_ratio > 2
  "пробой максимумов" / "breakouts"         → run_screen, close > highest(high, 20)
  "сжатие" / "squeeze candidates"           → run_screen, bb_width < 3
  "сильный тренд" / "trending stocks"       → run_screen, adx > 30
  "самые волатильные" / "most volatile"     → run_screen or run_compare, order by range_pct

Compare patterns:
  "кто волатильнее" / "more volatile"       → run_compare metrics, range_pct + atr
  "коррелируют" / "correlation"             → run_compare correlation
  "кто лучше" / "better performer"          → run_compare metrics, cumulative return
  "сравни рейнджи" / "compare ranges"       → run_compare metrics, range stats
</trading_knowledge>
```

### Новые примеры для промпта

```xml
<examples>
...existing examples...

Example 6 — screener (natural language → indicator):
User: Какие акции сейчас перепроданы?
Assistant: Ищу перепроданные акции в S&P 500...
→ run_screen({universe: "sp500", query: {map: {rsi: "rsi(close,14)"},
   where: "rsi < 30", select: "close, rsi", order_by: "rsi ASC"},
   title: "Oversold S&P 500"})
Assistant: 7 акций с RSI ниже 30. INTC самая перепроданная (RSI 18.7).

Example 7 — compare:
User: NQ или ES — что волатильнее?
Assistant: Сравниваю NQ и ES...
→ run_compare({instruments: ["NQ", "ES"], 
   query: {session: "RTH", period: "2024",
   map: {r: "range_pct()"}, select: "mean(r), max(r)"},
   compare_mode: "metrics", title: "NQ vs ES volatility"})
Assistant: NQ в 1.5 раза волатильнее — средний рейндж 1.82% vs 1.24%.

Example 8 — screener → deep dive:
User: Где вчера был необычный объём?
Assistant: [screener results: TSLA, NVDA, AMD]
User: Расскажи про TSLA подробнее
Assistant: [switches context to TSLA]
→ run_query({... TSLA daily stats ...})
</examples>
```

---

## Data Management

### Ежедневное обновление

```
Cron job (каждую ночь после close):
  1. Загрузить новые данные для всех инструментов
  2. Обновить minute data files
  3. Rebuild daily bars cache
  4. Обновить data_end в instrument configs
```

```python
# scripts/daily_update.py

async def daily_update():
    """Nightly data update pipeline."""
    symbols = get_all_tracked_symbols()
    
    for symbol in symbols:
        # 1. Fetch today's data
        new_data = await fetch_daily_data(symbol)
        
        # 2. Append to minute data
        append_minute_data(symbol, new_data)
        
        # 3. Rebuild daily cache
        rebuild_daily_cache(symbol)
    
    # 4. Update data_end dates
    update_instrument_configs()
    
    log.info(f"Updated {len(symbols)} instruments")
```

### Storage

```
data/
  minute/                # Raw minute bars (source of truth)
    NQ.parquet           # ~200MB per instrument (18 years × 1440 min/day)
    ES.parquet
    AAPL.parquet
    ...
  
  daily_cache/           # Pre-computed daily bars (for screener speed)
    NQ.parquet           # ~500KB per instrument
    ES.parquet
    AAPL.parquet
    ...

Estimates:
  Futures (20 instruments): ~4GB minute, 10MB daily cache
  S&P 500 (503 instruments): ~100GB minute, 250MB daily cache
  Crypto (20 instruments): ~4GB minute, 10MB daily cache
  Total: ~110GB minute, ~270MB daily cache
```

### Incremental vs Full

Minute data растёт каждый день. Стратегии:
- **Phase 1:** Только фьючерсы (20 инструментов, ~4GB). Управляемо.
- **Phase 2:** + Mag 7 / Top 50 акций. ~14GB. Управляемо.
- **Phase 3:** + S&P 500. ~110GB. Нужен серьёзный storage.
- **Alternative:** Для акций хранить только daily bars (не minute). 503 × 500KB = 250MB. Скринер работает, intraday аналитика нет.

---

## Design Decisions

| Вопрос | Решение | Почему |
|--------|---------|--------|
| Screener timeframe | Только daily | 99% скринер-запросов на daily. Intraday screener — huge complexity, tiny value |
| Universe size | Max 500 (v1) | 500 × 15ms = 7.5s. Приемлемо. 5000 — нужна другая архитектура |
| Screener snapshot | Last row (default) или aggregate | Большинство скринеров: "какой RSI сейчас" → last row. "Кто вырос больше" → aggregate |
| Compare instruments | 2-10 | Больше 10 — это уже screener с order_by |
| Correlation method | Pearson | Стандарт. Spearman и другие — v2 |
| Data freshness | Yesterday's close | Ночное обновление. Real-time = другой бизнес |
| Cross-asset correlation | Inner join on date | Пропускаем дни когда один не торговал. Альтернатива — forward fill, но опасно |
| Storage for stocks | Daily bars only (v1) | 500KB vs 200MB per instrument. Screener работает, minute analytics нет |
| Custom universes | List of symbols | Watchlists — v2. Сейчас: либо preset, либо перечислил тикеры |
| Click on symbol | Switch context | Естественный flow: screen → pick → deep dive |

---

## Взаимодействие с существующими модулями

### Functions — без изменений

Все 107 функций работают одинаково для run_query, run_screen, run_compare. Пайплайн `expressions.py` + `interpreter.py` переиспользуется. Новых функций не нужно.

Единственная новая функция (опционально):

```python
# Может быть полезна для compare
"relative_strength": lambda df, col, benchmark: col / benchmark
# Но это просто деление — не нужна отдельная функция
```

### Backtest — будущая интеграция

```
Screen → найти перепроданные акции → 
  выбрать INTC →
    backtest: "лонг при RSI < 30, стоп 5%, тейк 10%"
```

Screener как **источник идей**, backtest как **проверка**. Это полный workflow.

### Annotations — работают автоматически

Screener results содержат даты → `check_dates_for_holidays()` и `check_dates_for_events()` аннотируют результаты. Для screener это менее критично (snapshot, не time series), но для compare по дням — важно.

---

## Implementation Plan

### Phase 1: Compare (проще, меньше data)

- [ ] `barb/compare/engine.py` — metrics compare + correlation
- [ ] `barb/compare/metrics.py` — correlation, alignment
- [ ] `assistant/tools/compare.py` — tool wrapper
- [ ] Unit tests: correlation known values, metric aggregation
- [ ] Frontend: Compare Results Card, Correlation Card (scatter plot)

Compare работает на **уже имеющихся** инструментах. Если есть NQ и ES — compare уже полезен. Не нужен новый data pipeline.

### Phase 2: Screener (data foundation)

- [ ] `barb/screener/universe.py` — universe definitions, resolve
- [ ] `barb/screener/cache.py` — daily bars cache, rebuild script
- [ ] `barb/screener/engine.py` — screen loop, parallel execution
- [ ] `scripts/daily_update.py` — nightly data update
- [ ] Data: загрузить daily bars для futures (20 instruments)
- [ ] Unit tests: universe resolution, screen pipeline
- [ ] Frontend: Screener Results Card, progress bar, clickable symbols

### Phase 3: Expand Data

- [ ] Data: загрузить Mag 7 + Top 50 акций
- [ ] Data: загрузить Crypto Top 20
- [ ] Universe definitions для новых групп
- [ ] SSE streaming progress для больших universes

### Phase 4: Enhancements

- [ ] Saved screens (watchlists с автоматическим скринингом)
- [ ] Alerts: "уведоми когда RSI < 30 на любой акции из watchlist"
- [ ] Cross-asset correlation matrix (heatmap)
- [ ] Rolling correlation (time series of correlation)
- [ ] Sector rotation analysis
- [ ] Relative strength ranking
- [ ] Custom universes (user-defined watchlists)