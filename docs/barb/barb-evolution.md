# Barb Script: от Query Language к Trading Language

## Где мы сейчас

Barb Script — декларативный JSON + expressions. 46 функций, 9-step pipeline. Работает на одном инструменте, отвечает на аналитические вопросы.

```
Пользователь → Claude → Barb Script JSON → Interpreter → Pandas → Результат
```

Это хорошо для: "покажи дни когда NQ упал >2.5%", "средний рейндж по дням недели".

Это не может: "найди все акции с RSI < 30", "протестируй стратегию на MACD crossover", "покажи корреляцию AAPL и SPY".

## Где нужно быть

Bloomberg terminal даёт:
1. Любые данные по любому инструменту — мгновенно
2. Скрининг по всему рынку — "покажи что сегодня интересного"
3. Технический анализ — полный набор индикаторов
4. Бэктесты — проверить идею на истории
5. Сравнение инструментов — корреляции, спреды, relative strength

Barb может реалистично покрыть 1-5. Для этого нужны три вещи: **индикаторы**, **скрининг**, **мульти-инструмент**.

---

## Проблема 1: Выражения слишком низкоуровневые

### Сейчас

Чтобы Claude посчитал RSI, он должен написать:

```json
{
  "map": {
    "delta": "close - prev(close)",
    "gain": "if(delta > 0, delta, 0)",
    "loss": "if(delta < 0, abs(delta), 0)",
    "avg_gain": "rolling_mean(gain, 14)",
    "avg_loss": "rolling_mean(loss, 14)",
    "rs": "avg_gain / avg_loss",
    "rsi": "100 - 100 / (1 + rs)"
  }
}
```

7 промежуточных колонок. Каждая — шанс ошибиться. И это даже не настоящий RSI (Wilder's smoothing, не SMA).

### Нужно

```json
{
  "map": {
    "rsi": "rsi(close, 14)"
  }
}
```

Одна строка, одна функция, правильная реализация внутри.

### Какие функции добавить

**Индикаторы тренда:**

| Функция | Пример | Что делает |
|---------|--------|-----------|
| `sma(col, n)` | `sma(close, 20)` | Simple Moving Average. Алиас для rolling_mean, но привычнее трейдерам |
| `ema(col, n)` | `ema(close, 20)` | Уже есть ✅ |
| `wma(col, n)` | `wma(close, 20)` | Weighted Moving Average |
| `vwap_day()` | `vwap_day()` | VWAP (Volume Weighted Average Price) за день |
| `supertrend(n, mult)` | `supertrend(10, 3)` | SuperTrend индикатор |

**Осцилляторы:**

| Функция | Пример | Что делает |
|---------|--------|-----------|
| `rsi(col, n)` | `rsi(close, 14)` | RSI с Wilder's smoothing |
| `stoch_k(n)` | `stoch_k(14)` | Stochastic %K |
| `stoch_d(n, smooth)` | `stoch_d(14, 3)` | Stochastic %D |
| `cci(n)` | `cci(20)` | Commodity Channel Index |
| `williams_r(n)` | `williams_r(14)` | Williams %R |
| `mfi(n)` | `mfi(14)` | Money Flow Index |

**MACD (возвращает компоненты):**

| Функция | Пример | Что делает |
|---------|--------|-----------|
| `macd(col, fast, slow)` | `macd(close, 12, 26)` | MACD line |
| `macd_signal(col, fast, slow, sig)` | `macd_signal(close, 12, 26, 9)` | Signal line |
| `macd_hist(col, fast, slow, sig)` | `macd_hist(close, 12, 26, 9)` | Histogram |

**Волатильность:**

| Функция | Пример | Что делает |
|---------|--------|-----------|
| `atr(n)` | `atr(14)` | Average True Range (использует high, low, close из df) |
| `true_range()` | `true_range()` | True Range одного бара |
| `bb_upper(col, n, std)` | `bb_upper(close, 20, 2)` | Bollinger upper band |
| `bb_lower(col, n, std)` | `bb_lower(close, 20, 2)` | Bollinger lower band |
| `bb_mid(col, n)` | `bb_mid(close, 20)` | Bollinger middle (= SMA) |
| `keltner_upper(n, mult)` | `keltner_upper(20, 1.5)` | Keltner Channel upper |
| `keltner_lower(n, mult)` | `keltner_lower(20, 1.5)` | Keltner Channel lower |
| `donchian_upper(n)` | `donchian_upper(20)` | Donchian Channel high |
| `donchian_lower(n)` | `donchian_lower(20)` | Donchian Channel low |

**Объём:**

| Функция | Пример | Что делает |
|---------|--------|-----------|
| `obv()` | `obv()` | On Balance Volume |
| `vwap_day()` | `vwap_day()` | Intraday VWAP |
| `ad_line()` | `ad_line()` | Accumulation/Distribution |
| `volume_ratio(n)` | `volume_ratio(20)` | Текущий volume / SMA(volume, n) |

**Convenience (сахар, но критично для LLM reliability):**

| Функция | Пример | Эквивалент |
|---------|--------|-----------|
| `gap()` | `gap()` | `open - prev(close)` |
| `gap_pct()` | `gap_pct()` | `(open - prev(close)) / prev(close) * 100` |
| `change(col, n)` | `change(close, 1)` | `col - prev(col, n)` |
| `change_pct(col, n)` | `change_pct(close, 1)` | `(col - prev(col, n)) / prev(col, n) * 100` |
| `range()` | `range()` | `high - low` |
| `range_pct()` | `range_pct()` | `(high - low) / low * 100` |
| `body()` | `body()` | `close - open` |
| `body_pct()` | `body_pct()` | `(close - open) / open * 100` |
| `upper_wick()` | `upper_wick()` | `high - max(open, close)` |
| `lower_wick()` | `lower_wick()` | `min(open, close) - low` |
| `midpoint()` | `midpoint()` | `(high + low) / 2` |
| `typical_price()` | `typical_price()` | `(high + low + close) / 3` |
| `crossover(a, b)` | `crossover(ema(close,9), ema(close,21))` | `prev(a) <= prev(b) and a > b` |
| `crossunder(a, b)` | `crossunder(rsi(close,14), 70)` | `prev(a) >= prev(b) and a < b` |
| `highest(col, n)` | `highest(high, 20)` | Алиас для `rolling_max` |
| `lowest(col, n)` | `lowest(low, 20)` | Алиас для `rolling_min` |
| `inside_bar()` | `inside_bar()` | `high < prev(high) and low > prev(low)` |
| `outside_bar()` | `outside_bar()` | `high > prev(high) and low < prev(low)` |
| `green()` | `green()` | `close > open` |
| `red()` | `red()` | `close < open` |
| `doji(threshold)` | `doji(0.1)` | `abs(body_pct()) < threshold` |

### Принцип: implicit df access

Сейчас все функции получают `(df, *args)`. Индикаторы типа `atr()`, `gap()`, `true_range()` не требуют явных колонок — они берут OHLCV из df напрямую. Это уже работает (см. `dayofweek`, `count`), нужно просто расширить:

```python
# Уже есть такой паттерн:
"dayofweek": lambda df: pd.Series(df.index.dayofweek, index=df.index),

# Новые функции в том же стиле:
"gap": lambda df: df["open"] - df["close"].shift(1),
"true_range": lambda df: pd.concat([
    df["high"] - df["low"],
    (df["high"] - df["close"].shift(1)).abs(),
    (df["low"] - df["close"].shift(1)).abs(),
], axis=1).max(axis=1),
```

Не нужно менять ни парсер, ни evaluator, ни interpreter. Просто новые записи в `FUNCTIONS`.

### Количественная оценка

Сейчас: ~46 функций, из них торговых ~0.
После: ~90-100 функций, из них торговых ~50.

Это звучит как много, но для LLM это не проблема — каждая функция описана в tool description один раз. Зато вместо 7 строк для RSI — одна. Меньше токенов, меньше ошибок.

---

## Проблема 2: Один инструмент за раз

### Сейчас

Каждый `run_query` работает на одном DataFrame (одном инструменте). Чтобы сравнить NQ и ES, Claude должен сделать два вызова и сопоставить результаты вручную в тексте.

### Для "Bloomberg for the poor" нужны два новых инструмента

#### 2a. Screener — `run_screen`

"Найди все акции где RSI < 30 и объём выше среднего"

```json
{
  "name": "run_screen",
  "input": {
    "universe": "sp500",          // или "all", "futures", "crypto", список тикеров
    "session": "RTH",
    "from": "daily",
    "map": {
      "rsi": "rsi(close, 14)",
      "vol_ratio": "volume_ratio(20)"
    },
    "where": "rsi < 30 and vol_ratio > 1.5",
    "select": "last(rsi), last(vol_ratio), last(close)",
    "sort": "rsi asc",
    "limit": 20
  }
}
```

Архитектурно: тот же пайплайн, но `execute()` вызывается для каждого инструмента в universe. Результат — таблица с колонкой `symbol`.

```
| symbol | close | rsi  | vol_ratio |
|--------|-------|------|-----------|
| AAPL   | 178.2 | 24.3 | 2.1       |
| NVDA   | 892.1 | 27.8 | 1.8       |
| TSLA   | 245.6 | 29.1 | 1.6       |
```

**Производительность:** 10K инструментов × daily resample ≈ 10K × ~50ms = ~500 секунд последовательно. Нужна параллелизация + кэш ежедневных агрегатов. Или: предрассчитывать daily bars для всех инструментов и хранить в одном wide Parquet.

**Реализация (фазы):**
- **v1:** Фиксированные universes (sp500, nasdaq100, futures). Параллельный execute. SSE streaming прогресса.
- **v2:** Custom universes, предрассчитанные daily/weekly таблицы для мгновенного скрининга.

#### 2b. Compare — `run_compare`

"Сравни дневные рейнджи NQ и ES за 2024"

```json
{
  "name": "run_compare",
  "input": {
    "instruments": ["NQ", "ES"],
    "session": "RTH",
    "period": "2024",
    "from": "daily",
    "map": {
      "range_pct": "range_pct()"
    },
    "compare": "mean(range_pct)"     // что сравниваем
  }
}
```

Результат:

```
| symbol | mean_range_pct | std_range_pct | days |
|--------|---------------|---------------|------|
| NQ     | 1.82          | 0.95          | 251  |
| ES     | 1.24          | 0.68          | 251  |
```

Или для корреляции:

```json
{
  "instruments": ["AAPL", "SPY"],
  "from": "daily",
  "period": "2024",
  "compare": "correlation(close)"
}
```

→ `0.87`

---

## Проблема 3: Бэктест как часть языка

### Сейчас (из backtest.md)

Бэктест — отдельный tool `run_backtest` со своей стратегией. Это правильно. Но entry/exit conditions используют те же expressions что и `run_query`. Это значит все новые торговые функции автоматически доступны в бэктестах:

```
"Шорт когда RSI > 70 и MACD histogram отрицательный, стоп 1 ATR, тейк 2 ATR"

→ run_backtest({
    strategy: {
      entry: "rsi(close, 14) > 70 and macd_hist(close, 12, 26, 9) < 0",
      direction: "short",
      stop_loss: "atr(14)",        // динамический стоп в ATR
      take_profit: "atr(14) * 2"   // динамический тейк
    }
  })
```

### Динамические стопы/тейки

Сейчас `stop_loss` и `take_profit` — число или процент. Но трейдеры часто используют ATR-based стопы. Нужно поддержать expressions:

```python
stop_loss: float | str   # число, "1%", или expression "atr(14)"
take_profit: float | str  # число, "2%", или expression "atr(14) * 2"
```

Expression вычисляется на баре входа и фиксируется для всей сделки.

---

## Дорожная карта

### Phase 1: Trading Functions (делает Barb Script мощным)

Добавить в functions.py ~40-50 торговых функций. Не трогаем парсер, evaluator, interpreter — только новые записи в dict.

Приоритет:
1. **Convenience** — gap, change_pct, range, crossover, body (мгновенный эффект, LLM перестаёт ошибаться)
2. **Осцилляторы** — rsi, stoch, cci (самые популярные, нужны для скрининга и бэктестов)
3. **Волатильность** — atr, true_range, bollinger, keltner (нужны для динамических стопов)
4. **Тренд** — macd, supertrend, adx (для стратегий)
5. **Объём** — obv, vwap, volume_ratio (для скрининга)

Результат: Barb Script покрывает 90% того что даёт PineScript в плане индикаторов.

### Phase 2: Backtest Engine (делает Barb полезным)

Реализовать backtest.md. С динамическими стопами (ATR-based). С equity curve.

Результат: "Протестируй любую стратегию на любом инструменте одним вопросом."

### Phase 3: Screener (делает Barb уникальным)

`run_screen` — запрос по universe инструментов. Начать с малого (100 инструментов), потом масштабировать.

Результат: "Найди мне акции с RSI < 30 и объёмом выше среднего."

### Phase 4: Compare (делает Barb Bloomberg-like)

`run_compare` — сравнение инструментов, корреляции, спреды.

Результат: "Покажи корреляцию AAPL и SPY за 2024."

---

## Что НЕ менять

Текущая архитектура правильная. Не нужно трогать:

- **AST парсер** (expressions.py) — уже поддерживает всё что нужно
- **Evaluator** — функции вызываются через `func(df, *args)`, новые функции просто добавляются в dict
- **Pipeline** (interpreter.py) — 9 шагов покрывают все query паттерны
- **Validation** — автоматически подхватит новые функции из FUNCTIONS dict
- **Принцип "LLM → JSON → Interpreter"** — это ядро архитектуры

## Итого

```
Сейчас:                          Цель:
┌──────────────┐                 ┌──────────────────────────┐
│ 1 инструмент │                 │ 10,000 инструментов      │
│ 46 функций   │                 │ ~100 функций             │
│ run_query    │                 │ run_query (аналитика)     │
│              │                 │ run_backtest (стратегии)  │
│              │                 │ run_screen (скрининг)     │
│              │                 │ run_compare (сравнение)   │
└──────────────┘                 └──────────────────────────┘
    Query Tool                     Trading Language
```

Каждый инструмент (tool) — это фасад над тем же Barb Script. Один язык expressions, один набор функций, один пайплайн. Разница только в том, как tool организует данные на входе и результат на выходе.