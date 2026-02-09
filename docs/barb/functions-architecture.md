# Functions Architecture

Barb Script functions — единственная часть системы, которую нужно существенно расширить. Парсер, evaluator, interpreter, validation — не меняются.

## Принцип №1: совпадение с TradingView

Трейдер откроет TradingView, посмотрит RSI(14) на NQ — увидит 62.34. Потом спросит Barb "покажи RSI" — и увидит 62.34. Если увидит 61.87 — доверие потеряно навсегда.

Поэтому:
- Референс для каждого индикатора — **TradingView PineScript** (`ta.rsi`, `ta.atr`, etc.)
- Все дефолты следуют TradingView, не ta-lib (они расходятся: Stochastic %K = 14 в TV vs 5 в ta-lib, CCI = 20 в TV vs 14 в ta-lib)
- Тесты сверяются с реальными значениями из TradingView
- Расхождение > 0.1 на 100+ барах = баг

---

## Как работает сейчас

Один файл `barb/functions.py`. Dict `FUNCTIONS` маппит имена на callables. Каждая функция: `(df, *args) → Series | scalar`.

```python
FUNCTIONS = {
    "abs": lambda df, x: x.abs() if isinstance(x, pd.Series) else abs(x),
    "prev": lambda df, col, n=1: col.shift(int(n)),
    "rolling_mean": lambda df, col, n: col.rolling(int(n)).mean(),
    "dayofweek": lambda df: pd.Series(df.index.dayofweek, index=df.index),
    ...
}
```

46 функций. Все generic — ни одной трейдерской. Чтобы посчитать RSI, Claude пишет 7 строк выражений и всё равно получает неточный результат (SMA вместо Wilder's smoothing).

---

## Фундамент: _wilder_smooth()

Три главных индикатора (RSI, ATR, ADX) используют Wilder's smoothing. TradingView реализует его как `ta.rma()`: первое значение = SMA первых N баров, дальше рекурсивная формула. Наивный `ewm(alpha=1/n)` даёт расхождение в первых ~100 барах.

### Проблема с pandas ewm()

```python
# Это НЕ совпадает с TradingView:
col.ewm(alpha=1/n, adjust=False).mean()
# pandas начинает экспоненциальное взвешивание с первого бара
# TradingView сидит первое значение SMA, потом переключается на рекурсию
```

### Правильная реализация

```python
# barb/functions/_smoothing.py

import numpy as np
import pandas as pd


def wilder_smooth(series: pd.Series, n: int) -> pd.Series:
    """Wilder's smoothing (RMA) — exact TradingView ta.rma() match.

    First value = SMA of first n points.
    Subsequent: rma[t] = (1/n) * value[t] + (1 - 1/n) * rma[t-1]

    This is NOT the same as ewm(alpha=1/n, adjust=False).
    The SMA seed is what makes TradingView values match.
    """
    n = int(n)
    result = np.full(len(series), np.nan)
    values = series.values

    # Find first window of n non-NaN values for SMA seed
    count = 0
    seed_end = -1
    for i in range(len(values)):
        if not np.isnan(values[i]):
            count += 1
            if count == n:
                seed_end = i
                break

    if seed_end == -1:
        return pd.Series(result, index=series.index)

    # SMA seed
    seed_start = seed_end - n + 1
    # Collect n non-NaN values ending at seed_end
    non_nan_vals = []
    idx = 0
    for i in range(len(values)):
        if not np.isnan(values[i]):
            non_nan_vals.append(values[i])
            if len(non_nan_vals) == n:
                seed_end = i
                break

    result[seed_end] = np.mean(non_nan_vals)

    # Recursive Wilder's
    alpha = 1.0 / n
    for i in range(seed_end + 1, len(values)):
        if np.isnan(values[i]):
            result[i] = result[i - 1]
        else:
            result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]

    return pd.Series(result, index=series.index)
```

### Три типа smoothing в Barb

| Тип | Формула | Pandas | Используется |
|-----|---------|--------|-------------|
| **Wilder's / RMA** | α = 1/n, SMA seed | `wilder_smooth(col, n)` | RSI, ATR, ADX, +DI, -DI |
| **Standard EMA** | α = 2/(n+1) | `ewm(span=n, adjust=False)` | MACD, Keltner center, обычные EMA |
| **SMA** | простое среднее | `rolling(n).mean()` | Bollinger center, Stochastic %D |

**Критически важно:** `adjust=False` всегда. Pandas дефолт `adjust=True` не совпадает ни с одной торговой платформой.

---

## Новая структура

```
barb/
  functions/
    __init__.py           # Собирает FUNCTIONS dict, экспортирует AGGREGATE_FUNCS
    _smoothing.py         # wilder_smooth() — фундамент для RSI, ATR, ADX
    core.py               # Скалярные: abs, log, sqrt, sign, round, if
    lag.py                # Сдвиги: prev, next
    window.py             # Окна: rolling_mean/sum/max/min/std, rolling_count, ema, sma, wma, hma, vwma, rma
    cumulative.py         # Кумулятивные: cumsum, cummax, cummin
    pattern.py            # Паттерны: streak, bars_since, rank, rising, falling, valuewhen, pivothigh, pivotlow
    aggregate.py          # Агрегатные: mean, sum, count, max, min, std, median, percentile, correlation, last
    time.py               # Временные: dayofweek, hour, month, year, etc.
    convenience.py        # Торговый сахар: gap, change_pct, body, crossover, inside_bar, ...
    oscillators.py        # RSI, Stochastic, CCI, Williams %R, MFI, ROC, Momentum
    trend.py              # MACD, ADX, SuperTrend, Parabolic SAR
    volatility.py         # ATR, True Range, Bollinger, Keltner, Donchian
    volume.py             # OBV, VWAP, A/D Line, Volume Ratio
```

### __init__.py

```python
"""Barb Script function registry.

All functions receive (df, *args) where df is the current DataFrame.
New functions are added to category modules — they appear in Barb Script automatically.
"""

from barb.functions.core import CORE_FUNCTIONS
from barb.functions.lag import LAG_FUNCTIONS
from barb.functions.window import WINDOW_FUNCTIONS
from barb.functions.cumulative import CUMULATIVE_FUNCTIONS
from barb.functions.pattern import PATTERN_FUNCTIONS
from barb.functions.aggregate import AGGREGATE_FUNCTIONS, AGGREGATE_FUNCS
from barb.functions.time import TIME_FUNCTIONS
from barb.functions.convenience import CONVENIENCE_FUNCTIONS
from barb.functions.oscillators import OSCILLATOR_FUNCTIONS
from barb.functions.trend import TREND_FUNCTIONS
from barb.functions.volatility import VOLATILITY_FUNCTIONS
from barb.functions.volume import VOLUME_FUNCTIONS

FUNCTIONS = {
    **CORE_FUNCTIONS,
    **LAG_FUNCTIONS,
    **WINDOW_FUNCTIONS,
    **CUMULATIVE_FUNCTIONS,
    **PATTERN_FUNCTIONS,
    **AGGREGATE_FUNCTIONS,
    **TIME_FUNCTIONS,
    **CONVENIENCE_FUNCTIONS,
    **OSCILLATOR_FUNCTIONS,
    **TREND_FUNCTIONS,
    **VOLATILITY_FUNCTIONS,
    **VOLUME_FUNCTIONS,
}
```

Validation.py импортирует `FUNCTIONS` как и раньше — ничего не ломается.

---

## Существующие функции (рефакторинг)

Текущие 46 функций разносятся по файлам без изменения логики.

### core.py — 6 функций

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `abs(x)` | `(df, x)` | Абсолютное значение |
| `log(x)` | `(df, x)` | Натуральный логарифм |
| `sqrt(x)` | `(df, x)` | Квадратный корень |
| `sign(x)` | `(df, x)` | Знак: -1, 0, 1 |
| `round(x, n)` | `(df, x, n=0)` | Округление до n знаков |
| `if(cond, then, else)` | `(df, cond, then, else_)` | Условный выбор поэлементно |

### lag.py — 2 функции

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `prev(col, n)` | `(df, col, n=1)` | Значение N баров назад |
| `next(col, n)` | `(df, col, n=1)` | Значение N баров вперёд |

### window.py — 12 функций

Существующие 7 + новые 5 (алиасы и moving averages).

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `rolling_mean(col, n)` | `(df, col, n)` | Скользящее среднее |
| `rolling_sum(col, n)` | `(df, col, n)` | Скользящая сумма |
| `rolling_max(col, n)` | `(df, col, n)` | Скользящий максимум |
| `rolling_min(col, n)` | `(df, col, n)` | Скользящий минимум |
| `rolling_std(col, n)` | `(df, col, n)` | Скользящее стд. отклонение |
| `rolling_count(cond, n)` | `(df, cond, n)` | Кол-во true за окно |
| `ema(col, n)` | `(df, col, n)` | Standard EMA: `ewm(span=n, adjust=False)` |
| `sma(col, n)` | `(df, col, n)` | **NEW** Алиас для rolling_mean |
| `wma(col, n)` | `(df, col, n)` | **NEW** Weighted Moving Average |
| `hma(col, n)` | `(df, col, n)` | **NEW** Hull Moving Average |
| `vwma(n)` | `(df, n)` | **NEW** Volume Weighted MA — implicit OHLCV |
| `rma(col, n)` | `(df, col, n)` | **NEW** Wilder's smoothing (= `ta.rma()` в PineScript) |

**Алиасы** (трейдерские имена):

| Функция | Алиас для |
|---------|----------|
| `sma(col, n)` | `rolling_mean(col, n)` |
| `highest(col, n)` | `rolling_max(col, n)` |
| `lowest(col, n)` | `rolling_min(col, n)` |

### cumulative.py — 3 функции (без изменений)

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `cummax(col)` | `(df, col)` | Кумулятивный максимум |
| `cummin(col)` | `(df, col)` | Кумулятивный минимум |
| `cumsum(col)` | `(df, col)` | Кумулятивная сумма |

### pattern.py — 8 функций (было 3, +5 новых)

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `streak(cond)` | `(df, cond)` | Кол-во подряд true. Сброс на false |
| `bars_since(cond)` | `(df, cond)` | Баров с последнего true. NaN если никогда |
| `rank(col)` | `(df, col)` | Перцентильный ранг (0-1) |
| `rising(col, n)` | `(df, col, n)` | **NEW** True если col растёт N баров подряд |
| `falling(col, n)` | `(df, col, n)` | **NEW** True если col падает N баров подряд |
| `valuewhen(cond, col, n)` | `(df, cond, col, n=0)` | **NEW** Значение col когда cond был true N-ый раз назад |
| `pivothigh(n_left, n_right)` | `(df, n_left, n_right)` | **NEW** Локальный максимум high (NaN где нет пивота) |
| `pivotlow(n_left, n_right)` | `(df, n_left, n_right)` | **NEW** Локальный минимум low |

### aggregate.py — 10 функций (без изменений)

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `mean(col)` | `(df, col)` | Среднее |
| `sum(col)` | `(df, col)` | Сумма |
| `max(col)` | `(df, col)` | Максимум |
| `min(col)` | `(df, col)` | Минимум |
| `std(col)` | `(df, col)` | Стд. отклонение |
| `median(col)` | `(df, col)` | Медиана |
| `count()` | `(df)` | Количество строк |
| `percentile(col, p)` | `(df, col, p)` | Перцентиль (0-1) |
| `correlation(col1, col2)` | `(df, col1, col2)` | Корреляция Пирсона |
| `last(col)` | `(df, col)` | Последнее значение |

### time.py — 10 функций (без изменений)

| Функция | Возвращает |
|---------|-----------|
| `dayofweek()` | 0 (Пн) — 4 (Пт) |
| `dayname()` | "Monday", "Tuesday", ... |
| `hour()` | 0-23 |
| `minute()` | 0-59 |
| `month()` | 1-12 |
| `monthname()` | "January", "February", ... |
| `year()` | 2008, 2024, ... |
| `date()` | datetime.date объекты |
| `day()` | 1-31 |
| `quarter()` | 1-4 |

---

## Новые функции

### Контракт

Каждая новая функция:
- Сигнатура `(df, *args) → pd.Series | scalar` — как все существующие
- Берёт OHLCV из `df` напрямую когда нужно (`df["high"]`, `df["close"]`, etc.)
- Возвращает Series с тем же index что и df
- NaN для начальных баров где недостаточно данных (rolling window warmup)
- Не мутирует df
- **Значения совпадают с TradingView с точностью < 0.1 после 100 баров warmup**

### convenience.py — торговый сахар (~20 функций)

Короткие обёртки. Каждая 1-3 строки. Критичны для LLM reliability — Claude пишет `gap()` вместо `open - prev(close)` и не ошибается.

**Price helpers:**

| Функция | Сигнатура | Реализация |
|---------|-----------|------------|
| `gap()` | `(df)` | `df["open"] - df["close"].shift(1)` |
| `gap_pct()` | `(df)` | `(df["open"] - df["close"].shift(1)) / df["close"].shift(1) * 100` |
| `change(col, n)` | `(df, col, n=1)` | `col - col.shift(int(n))` |
| `change_pct(col, n)` | `(df, col, n=1)` | `(col - col.shift(int(n))) / col.shift(int(n)) * 100` |
| `range()` | `(df)` | `df["high"] - df["low"]` |
| `range_pct()` | `(df)` | `(df["high"] - df["low"]) / df["low"] * 100` |
| `midpoint()` | `(df)` | `(df["high"] + df["low"]) / 2` |
| `typical_price()` | `(df)` | `(df["high"] + df["low"] + df["close"]) / 3` |

**Candle helpers:**

| Функция | Сигнатура | Реализация |
|---------|-----------|------------|
| `body()` | `(df)` | `df["close"] - df["open"]` |
| `body_pct()` | `(df)` | `(df["close"] - df["open"]) / df["open"] * 100` |
| `upper_wick()` | `(df)` | `df["high"] - df[["open", "close"]].max(axis=1)` |
| `lower_wick()` | `(df)` | `df[["open", "close"]].min(axis=1) - df["low"]` |
| `green()` | `(df)` | `df["close"] > df["open"]` (boolean Series) |
| `red()` | `(df)` | `df["close"] < df["open"]` (boolean Series) |
| `doji(threshold)` | `(df, threshold=0.1)` | `body().abs() / range() < threshold` |
| `inside_bar()` | `(df)` | `(df["high"] < df["high"].shift(1)) & (df["low"] > df["low"].shift(1))` |
| `outside_bar()` | `(df)` | `(df["high"] > df["high"].shift(1)) & (df["low"] < df["low"].shift(1))` |

**Signal helpers:**

| Функция | Сигнатура | Реализация |
|---------|-----------|------------|
| `crossover(a, b)` | `(df, a, b)` | `(a.shift(1) <= b.shift(1)) & (a > b)` |
| `crossunder(a, b)` | `(df, a, b)` | `(a.shift(1) >= b.shift(1)) & (a < b)` |

### oscillators.py (~8 функций)

Все дефолты следуют TradingView.

**RSI — правильная реализация с SMA seed:**

```python
from barb.functions._smoothing import wilder_smooth

def _rsi(df, col, n=14):
    """RSI с Wilder's smoothing — точное совпадение с TradingView ta.rsi().

    rsi(close, 14) → Series[0-100]
    """
    n = int(n)
    delta = col.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = wilder_smooth(gain, n)
    avg_loss = wilder_smooth(loss, n)

    rs = avg_gain / avg_loss
    rsi = 100 - 100 / (1 + rs)

    # Edge case: all gains (avg_loss = 0) → RSI = 100
    rsi = rsi.where(avg_loss != 0, 100.0)

    return rsi
```

**CCI — mean deviation, не std:**

```python
def _cci(df, n=20):
    """CCI = (TP - SMA(TP)) / (0.015 * MeanDeviation).
    Uses MEAN deviation, NOT standard deviation.
    Default n=20 matches TradingView (NOT ta-lib which defaults to 14).
    """
    n = int(n)
    tp = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = tp.rolling(n).mean()
    mean_dev = tp.rolling(n).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma_tp) / (0.015 * mean_dev)
```

**MFI — rolling sums, не exponential:**

```python
def _mfi(df, n=14):
    """Money Flow Index.
    Often described as "RSI on volume" — MISLEADING.
    MFI uses simple rolling sums, NOT exponential smoothing like RSI.
    """
    n = int(n)
    tp = (df["high"] + df["low"] + df["close"]) / 3
    rmf = tp * df["volume"]
    direction = tp.diff()
    pos_flow = rmf.where(direction > 0, 0.0).rolling(n).sum()
    neg_flow = rmf.where(direction < 0, 0.0).rolling(n).sum()
    return 100 - 100 / (1 + pos_flow / neg_flow)
```

| Функция | Сигнатура | TV дефолт | Заметки |
|---------|-----------|-----------|---------|
| `rsi(col, n)` | `(df, col, n=14)` | 14 | Wilder's smoothing с SMA seed |
| `stoch_k(n)` | `(df, n=14)` | **14** | ta-lib дефолт = 5! |
| `stoch_d(n, smooth)` | `(df, n=14, smooth=3)` | 14, 3 | %D = SMA(%K, smooth) |
| `cci(n)` | `(df, n=20)` | **20** | ta-lib дефолт = 14! Mean deviation, не std |
| `williams_r(n)` | `(df, n=14)` | 14 | Диапазон -100..0 |
| `mfi(n)` | `(df, n=14)` | 14 | Rolling sums, не exponential |
| `roc(col, n)` | `(df, col, n=1)` | — | Rate of Change % |
| `momentum(col, n)` | `(df, col, n=10)` | 10 | Абсолютное изменение |

### trend.py (~10 функций)

**MACD — standard EMA, не Wilder's:**

```python
def _macd(df, col, fast=12, slow=26):
    """MACD Line = EMA(fast) - EMA(slow).
    Uses STANDARD EMA (span-based), not Wilder's.
    """
    fast_ema = col.ewm(span=int(fast), adjust=False).mean()
    slow_ema = col.ewm(span=int(slow), adjust=False).mean()
    return fast_ema - slow_ema
```

**ADX — полный алгоритм с Wilder's:**

```python
from barb.functions._smoothing import wilder_smooth

def _adx_system(df, n=14):
    """Complete Directional Movement System.
    Returns (+DI, -DI, ADX).
    All smoothing uses wilder_smooth() for TradingView match.
    Total lookback = 2n - 1 bars (27 for n=14).
    """
    n = int(n)
    high, low, close = df["high"], df["low"], df["close"]

    # Step 1: Directional Movement
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(0.0, index=df.index)
    minus_dm = pd.Series(0.0, index=df.index)
    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

    # Step 2: Smooth +DM, -DM, TR with Wilder's
    tr = _true_range(df)
    smoothed_tr = wilder_smooth(tr, n)
    smoothed_plus_dm = wilder_smooth(plus_dm, n)
    smoothed_minus_dm = wilder_smooth(minus_dm, n)

    # Step 3: Directional Indicators
    plus_di = (smoothed_plus_dm / smoothed_tr) * 100
    minus_di = (smoothed_minus_dm / smoothed_tr) * 100

    # Step 4: DX
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100

    # Step 5: ADX = Wilder's smooth of DX
    adx = wilder_smooth(dx, n)

    return plus_di, minus_di, adx
```

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `macd(col, fast, slow)` | `(df, col, fast=12, slow=26)` | MACD line — standard EMA |
| `macd_signal(col, fast, slow, sig)` | `(df, col, fast=12, slow=26, sig=9)` | Signal line |
| `macd_hist(col, fast, slow, sig)` | `(df, col, fast=12, slow=26, sig=9)` | Histogram |
| `adx(n)` | `(df, n=14)` | Average Directional Index — Wilder's |
| `plus_di(n)` | `(df, n=14)` | +DI |
| `minus_di(n)` | `(df, n=14)` | -DI |
| `supertrend(n, mult)` | `(df, n=10, mult=3)` | SuperTrend с clamping и flip |
| `supertrend_dir(n, mult)` | `(df, n=10, mult=3)` | Direction: 1 (up) / -1 (down) |
| `sar(accel, max_accel)` | `(df, accel=0.02, max=0.2)` | Parabolic SAR — топ-10 индикатор |
| `wma(col, n)` | `(df, col, n)` | Weighted Moving Average |

### volatility.py (~12 функций)

**ATR с Wilder's smoothing:**

```python
from barb.functions._smoothing import wilder_smooth

def _true_range(df):
    """True Range = max(H-L, |H-prevC|, |L-prevC|)."""
    prev_close = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)

def _atr(df, n=14):
    """ATR = Wilder's smooth of True Range.
    Matches TradingView ta.atr() exactly via wilder_smooth().
    """
    return wilder_smooth(_true_range(df), int(n))
```

**Bollinger Bands — ddof=0 (population std):**

```python
def _bb_upper(df, col, n=20, mult=2):
    """Bollinger upper = SMA + mult * std.
    CRITICAL: ddof=0 (population std), NOT ddof=1 (sample).
    TradingView и ta-lib используют population std dev.
    Pandas default ddof=1 даёт более широкие полосы — НЕПРАВИЛЬНО.
    """
    mid = col.rolling(int(n)).mean()
    std = col.rolling(int(n)).std(ddof=0)  # population!
    return mid + float(mult) * std
```

**Keltner Channels — исправленные дефолты:**

```python
def _keltner_upper(df, ema_n=20, atr_n=10, mult=2):
    """Keltner upper = EMA(close, ema_n) + mult * ATR(atr_n).
    EMA period и ATR period — РАЗНЫЕ параметры.
    Defaults: ema=20, atr=10, mult=2.
    """
    mid = df["close"].ewm(span=int(ema_n), adjust=False).mean()
    atr = _atr(df, int(atr_n))
    return mid + float(mult) * atr
```

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `true_range()` | `(df)` | True Range одного бара |
| `atr(n)` | `(df, n=14)` | ATR — Wilder's smoothing |
| `natr(n)` | `(df, n=14)` | Normalized ATR: `atr / close * 100` |
| `bb_upper(col, n, mult)` | `(df, col, n=20, mult=2)` | Bollinger upper — **ddof=0** |
| `bb_lower(col, n, mult)` | `(df, col, n=20, mult=2)` | Bollinger lower — **ddof=0** |
| `bb_mid(col, n)` | `(df, col, n=20)` | Bollinger middle (= SMA) |
| `bb_width(col, n, mult)` | `(df, col, n=20, mult=2)` | Band width % — для squeeze |
| `bb_pct(col, n, mult)` | `(df, col, n=20, mult=2)` | %B — позиция цены в полосах |
| `keltner_upper(ema_n, atr_n, mult)` | `(df, 20, 10, 2)` | **FIXED** EMA + mult * ATR |
| `keltner_lower(ema_n, atr_n, mult)` | `(df, 20, 10, 2)` | **FIXED** EMA - mult * ATR |
| `donchian_upper(n)` | `(df, n=20)` | Highest high |
| `donchian_lower(n)` | `(df, n=20)` | Lowest low |

### volume.py (~5 функций)

**A/D Line — обработка zero-range баров:**

```python
def _ad_line(df):
    """Accumulation/Distribution Line.
    CLV = ((Close-Low) - (High-Close)) / (High-Low)
    Edge case: High == Low → CLV = 0.
    """
    high_low = df["high"] - df["low"]
    clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / high_low
    clv = clv.fillna(0)  # zero-range bars
    return (clv * df["volume"]).cumsum()
```

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `obv()` | `(df)` | On Balance Volume |
| `vwap_day()` | `(df)` | VWAP intraday с ресетом по дням |
| `ad_line()` | `(df)` | A/D Line — zero-range safe |
| `volume_ratio(n)` | `(df, n=20)` | volume / SMA(volume, n) |
| `volume_sma(n)` | `(df, n=20)` | SMA объёма |

---

## Принципы реализации

### 1. TradingView — единственный референс

| Индикатор | TradingView дефолт | ta-lib дефолт | Barb следует |
|-----------|-------------------|---------------|-------------|
| Stochastic %K | 14 | **5** | TradingView: 14 |
| CCI | 20 | **14** | TradingView: 20 |
| SuperTrend period | 10 | нет | TradingView: 10 |
| SuperTrend mult | 3 | нет | TradingView: 3 |
| Keltner EMA | 20 | — | 20 |
| Keltner ATR | 10 | — | 10 |
| Keltner mult | 2 | — | 2 |
| Bollinger std | population (ddof=0) | population | population |
| RSI smoothing | Wilder's (SMA seed) | Wilder's (SMA seed) | Wilder's (SMA seed) |
| ATR smoothing | Wilder's (SMA seed) | Wilder's (SMA seed) | Wilder's (SMA seed) |
| MACD EMA | standard span-based | standard span-based | standard span-based |

### 2. Implicit OHLCV access

```python
# Явные колонки — пользователь передаёт
"rsi": (df, col, n=14)        # rsi(close, 14) — любая колонка
"ema": (df, col, n)            # ema(close, 20) — любая колонка

# Implicit OHLCV — берёт из df
"atr": (df, n=14)              # atr(14) — всегда H/L/C
"gap": (df)                    # gap() — всегда O/C
"stoch_k": (df, n=14)          # stoch_k(14) — всегда H/L/C
```

Правило: если индикатор **всегда** работает с фиксированными колонками — implicit. Если колонка может быть любой — explicit.

### 3. Внутреннее переиспользование

```python
# volatility.py
from barb.functions._smoothing import wilder_smooth
def _atr(df, n=14):
    return wilder_smooth(_true_range(df), n)

# trend.py
from barb.functions.volatility import _true_range
def _adx_system(df, n=14):
    tr = _true_range(df)  # кросс-модульная зависимость
```

В FUNCTIONS dict — только публичные имена. `_rsi`, `_atr`, `_true_range` — private.

---

## Тестирование

### Структура

```
tests/
  functions/
    test_core.py
    test_window.py
    test_pattern.py
    test_convenience.py
    test_oscillators.py
    test_trend.py
    test_volatility.py
    test_volume.py
    test_smoothing.py         # wilder_smooth отдельно
    conftest.py               # make_df, load_test_data, load_reference
    reference_data/           # CSV с TradingView значениями
      nq_daily_rsi14.csv
      nq_daily_atr14.csv
      nq_daily_bb20.csv
      nq_daily_macd.csv
```

### TradingView match тест

```python
def test_rsi_matches_tradingview():
    """RSI(14) on NQ daily must match TradingView values."""
    df = load_test_data("NQ_daily")
    result = FUNCTIONS["rsi"](df, df["close"], 14)
    reference = load_reference("nq_daily_rsi14.csv")

    for date, expected in reference.items():
        actual = result.loc[date]
        assert abs(actual - expected) < 0.1, (
            f"RSI mismatch on {date}: got {actual:.2f}, expected {expected:.2f}"
        )
```

### Сбор reference data

1. Открыть TradingView, NQ daily chart
2. Добавить индикатор с дефолтными параметрами
3. Hover over 10+ точек, записать дату + значение
4. Сохранить в `tests/functions/reference_data/`

### Что тестировать обязательно

1. **TradingView match** — 10+ точек для RSI, ATR, MACD, Bollinger, Stochastic
2. **Границы** — RSI ∈ [0, 100], Stochastic ∈ [0, 100], Williams %R ∈ [-100, 0]
3. **NaN warmup** — RSI(14) первые 14 баров = NaN
4. **Edge cases** — all gains (RSI=100), zero-range bars (A/D), zero volume
5. **Пустой DataFrame** — не падает
6. **wilder_smooth vs ewm** — тест что SMA seed даёт другое первое значение

---

## Влияние на промпт

### Группированный список для tool description

```
Functions:

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
```

### Примеры в промпте

```
Q: "Покажи дни когда RSI ниже 30"
→ {"from": "daily", "map": {"rsi": "rsi(close, 14)"}, "where": "rsi < 30"}

Q: "Средний ATR по месяцам за 2024"
→ {"from": "daily", "period": "2024", "map": {"atr": "atr(14)", "m": "month()"},
   "group_by": "m", "select": "mean(atr)"}

Q: "MACD crossover signals"
→ {"from": "daily", "map": {"signal": "crossover(macd(close,12,26), macd_signal(close,12,26,9))"},
   "where": "signal"}

Q: "Bollinger squeeze — когда полосы сужаются"
→ {"from": "daily", "map": {"bw": "bb_width(close, 20, 2)"}, "where": "bw < 5", "limit": 20}
```

---

## Итого

### Счётчик функций

| Модуль | Было | Стало | Δ |
|--------|------|-------|---|
| core.py | 6 | 6 | 0 |
| lag.py | 2 | 2 | 0 |
| window.py | 7 | 12 | +5 (sma, wma, hma, vwma, rma) |
| cumulative.py | 3 | 3 | 0 |
| pattern.py | 3 | 8 | +5 (rising, falling, valuewhen, pivothigh, pivotlow) |
| aggregate.py | 10 | 10 | 0 |
| time.py | 10 | 10 | 0 |
| convenience.py | 0 | 20 | +20 |
| oscillators.py | 0 | 8 | +8 |
| trend.py | 0 | 10 | +10 |
| volatility.py | 0 | 12 | +12 |
| volume.py | 0 | 5 | +5 |
| _smoothing.py | 0 | 1 | +1 (wilder_smooth) |
| **Итого** | **41** | **107** | **+66** |

### Что меняется

| Компонент | Изменение |
|-----------|-----------|
| `barb/functions/` | 13 модулей вместо 1 файла (12 + _smoothing) |
| `barb/functions/_smoothing.py` | **NEW** — фундамент для RSI, ATR, ADX |
| `barb/functions/__init__.py` | Собирает FUNCTIONS dict |
| System prompt | Расширенный список функций + примеры |

### Что НЕ меняется

| Компонент | Почему |
|-----------|--------|
| `expressions.py` | Парсер работает с FUNCTIONS dict — ему всё равно что внутри |
| `interpreter.py` | Пайплайн не зависит от конкретных функций |
| `validation.py` | Автоматически видит новые функции через FUNCTIONS import |
| `assistant/` | Claude просто получает больше функций в tool description |
| `api/` | Не знает о функциях вообще |
| `frontend/` | Рендерит данные — ему всё равно как они посчитаны |

### Приоритет реализации

1. **_smoothing.py** — wilder_smooth() первым (всё остальное от него зависит)
2. **convenience.py** — мгновенный эффект: gap/change_pct/crossover/body
3. **oscillators.py** — RSI первым, проверить match с TradingView
4. **volatility.py** — ATR + true_range (нужны для бэктестов)
5. **trend.py** — MACD, ADX, SuperTrend, SAR
6. **volume.py** — OBV, volume_ratio (для скрининга)
7. **window.py дополнения** — hma, vwma, rma
8. **pattern.py дополнения** — pivots, valuewhen

### Ключевые исправления после ресёрча

| Что было неправильно | Что стало | Почему |
|---------------------|-----------|--------|
| `ewm(alpha=1/n)` для RSI/ATR | `wilder_smooth()` с SMA seed | Расхождение с TradingView в первых 100 барах |
| Bollinger std без ddof | `std(ddof=0)` population | TV и ta-lib используют population, pandas default = sample |
| Keltner `(n=20, mult=1.5)` | `(ema=20, atr=10, mult=2)` | Два отдельных периода, правильный множитель |
| CCI дефолт не зафиксирован | `cci(n=20)` | TV=20, ta-lib=14 — фиксируем TV |
| Stochastic дефолт не зафиксирован | `stoch_k(n=14)` | TV=14, ta-lib=5 — фиксируем TV |
| Нет Parabolic SAR | `sar(0.02, 0.2)` | Топ-10 индикатор у ритейл трейдеров |
| Нет pivot detection | `pivothigh/pivotlow` | Нужно для structure analysis |
| MFI описана как "RSI on volume" | Rolling sums, не exponential | Фундаментально другой алгоритм |
| Нет HMA, VWMA, RMA | Добавлены в window.py | PineScript базовые moving averages |
| Нет rising/falling | Добавлены в pattern.py | Есть в PineScript `ta.rising/ta.falling` |