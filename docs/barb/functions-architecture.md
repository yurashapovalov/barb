# Functions Architecture

Package `barb/functions/` — 106 функций в 12 модулях. Единственная часть системы, которая активно растёт. Парсер, evaluator, interpreter — не меняются.

## Принцип: совпадение с TradingView

Трейдер откроет TradingView, посмотрит RSI(14) на NQ — увидит 62.34. Потом спросит Barb — и должен увидеть 62.34. Расхождение > 0.1 после 100 баров = баг.

- Референс — **TradingView PineScript** (`ta.rsi`, `ta.atr`, etc.)
- Дефолты — TradingView, не ta-lib (Stochastic %K = 14 в TV vs 5 в ta-lib, CCI = 20 vs 14)
- Тесты сверяются с реальными значениями из TradingView

---

## Структура

```
barb/functions/
  __init__.py           # FUNCTIONS, SIGNATURES, DESCRIPTIONS, AGGREGATE_FUNCS
  _smoothing.py         # wilder_smooth() — фундамент для RSI, ATR, ADX
  core.py          (6)  # abs, log, sqrt, sign, round, if
  lag.py           (2)  # prev, next
  window.py       (12)  # rolling_*, ema, sma, wma, hma, vwma, rma
  cumulative.py    (3)  # cumsum, cummax, cummin
  pattern.py       (8)  # streak, bars_since, rank, rising, falling, valuewhen, pivothigh, pivotlow
  aggregate.py    (10)  # mean, sum, max, min, std, median, count, percentile, correlation, last
  time.py         (10)  # dayofweek, dayname, hour, minute, month, monthname, year, date, day, quarter
  convenience.py  (19)  # gap, change_pct, body, crossover, inside_bar, ...
  oscillators.py   (8)  # rsi, stoch_k, stoch_d, cci, williams_r, mfi, roc, momentum
  trend.py         (9)  # macd, macd_signal, macd_hist, adx, plus_di, minus_di, supertrend, supertrend_dir, sar
  volatility.py   (14)  # tr, atr, natr, bbands_*, kc_*, donchian_*
  volume.py        (5)  # obv, vwap_day, ad_line, volume_ratio, volume_sma
```

### Контракт функций

- Сигнатура: `(df, *args) → pd.Series | scalar`
- OHLCV из `df` напрямую когда нужно (`df["high"]`, `df["close"]`)
- Series с тем же index что и df
- NaN для начальных баров (rolling window warmup)
- Не мутирует df

### Три dict на модуль

Каждый модуль экспортирует `*_FUNCTIONS`, `*_SIGNATURES`, `*_DESCRIPTIONS`. `__init__.py` объединяет:

```python
FUNCTIONS = {**CORE_FUNCTIONS, **LAG_FUNCTIONS, ...}      # name → callable
SIGNATURES = {**CORE_SIGNATURES, **LAG_SIGNATURES, ...}   # name → "rsi(col, n=14)"
DESCRIPTIONS = {**CORE_DESCRIPTIONS, ...}                  # name → "Relative Strength Index..."
```

`SIGNATURES` и `DESCRIPTIONS` используются в `assistant/tools/reference.py` для auto-generated промпта. Добавил функцию в модуль → она появляется в Barb Script.

`AGGREGATE_FUNCS` — отдельный dict из aggregate.py (6 функций для group_by): `mean`, `sum`, `max`, `min`, `std`, `median`.

### Implicit vs explicit OHLCV

```python
# Explicit — пользователь передаёт колонку
"rsi": (df, col, n=14)        # rsi(close, 14)
"ema": (df, col, n)            # ema(close, 20)

# Implicit — берёт из df напрямую
"atr": (df, n=14)              # atr(14) — всегда H/L/C
"gap": (df)                    # gap() — всегда O/C
"stoch_k": (df, n=14)          # stoch_k(14) — всегда H/L/C
```

Правило: если индикатор **всегда** работает с фиксированными колонками — implicit. Если колонка может быть любой — explicit.

### Кросс-модульные зависимости

```python
# trend.py
from barb.functions.volatility import _atr, _tr
# adx_system использует _tr, supertrend использует _atr

# window.py (rma), oscillators.py, volatility.py, trend.py
from barb.functions._smoothing import wilder_smooth
```

В FUNCTIONS dict — только публичные имена. `_rsi`, `_atr`, `_tr` — private.

---

## Smoothing: три типа

| Тип | Формула | Pandas | Используется |
|-----|---------|--------|-------------|
| **Wilder's / RMA** | α = 1/n, SMA seed | `wilder_smooth(col, n)` | RSI, ATR, ADX, +DI, -DI |
| **Standard EMA** | α = 2/(n+1) | `ewm(span=n, adjust=False)` | MACD, Keltner, обычные EMA |
| **SMA** | простое среднее | `rolling(n).mean()` | Bollinger, Stochastic %D |

**Критически важно:** `adjust=False` всегда. Pandas дефолт `adjust=True` не совпадает ни с одной торговой платформой.

### Wilder's smoothing (`_smoothing.py`)

Наивный `ewm(alpha=1/n)` расходится с TradingView в первых ~100 барах. Причина: TradingView использует SMA seed:

```python
def wilder_smooth(series, n):
    # Первое значение = SMA первых n non-NaN точек
    result[seed_idx] = np.mean(non_nan)
    # Дальше рекурсия: rma[t] = (1/n) * val[t] + (1 - 1/n) * rma[t-1]
    for i in range(seed_idx + 1, len(values)):
        if np.isnan(values[i]):
            result[i] = result[i - 1]
        else:
            result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]
```

---

## Gotchas: что ломает TradingView matching

### Bollinger Bands: `ddof=0`

```python
std = col.rolling(n).std(ddof=0)  # population std — TradingView
# НЕ col.rolling(n).std()         # pandas default ddof=1 — sample std, полосы шире
```

### CCI: mean deviation, не std

```python
mean_dev = tp.rolling(n).apply(lambda x: abs(x - x.mean()).mean(), raw=True)
# НЕ tp.rolling(n).std()
```

### Keltner: два разных периода, mult=1.5

```python
kc_upper(n=20, atr_n=10, mult=1.5)   # EMA period ≠ ATR period, mult=1.5
# НЕ keltner(n=20, mult=2)            # один период, неправильный множитель
```

### MFI: rolling sums, не exponential

Часто описывается как "RSI on volume" — но алгоритм принципиально другой. MFI использует `rolling(n).sum()`, не exponential smoothing.

### TradingView vs ta-lib дефолты

| Индикатор | TradingView | ta-lib | Barb |
|-----------|-------------|--------|------|
| Stochastic %K | **14** | 5 | 14 |
| CCI | **20** | 14 | 20 |
| Bollinger std | ddof=0 | ddof=0 | ddof=0 |
| Keltner mult | **1.5** | — | 1.5 |
| RSI/ATR smoothing | Wilder's (SMA seed) | Wilder's | Wilder's |
| MACD EMA | standard span-based | standard | standard |

---

## Тестирование

### Структура

```
tests/functions/
  conftest.py               # shared df fixture (10-bar OHLCV DataFrame)
  test_core.py              # один test file на модуль
  test_lag.py
  test_window.py
  test_cumulative.py
  test_pattern.py
  test_aggregate.py
  test_time.py
  test_convenience.py
  test_oscillators.py
  test_trend.py
  test_volatility.py
  test_volume.py
  test_smoothing.py         # wilder_smooth отдельно
  test_registry.py          # FUNCTIONS/SIGNATURES/DESCRIPTIONS consistency
  test_tv_match.py          # сверка с TradingView на реальных данных NQ
  reference_data/
    nq_oscillators_tv.csv   # 3 даты × OHLCV + RSI/ATR/CCI/StochK/WilliamsR/MFI
```

### conftest.py — shared fixture

```python
@pytest.fixture
def df():
    """10-bar OHLCV DataFrame with DatetimeIndex."""
    dates = pd.date_range("2024-01-02", periods=10, freq="D")
    return pd.DataFrame({
        "open":   [100, 102, 101, 105, 103, 99, 104, 106, 102, 100],
        "high":   [105, 106, 104, 108, 107, 103, 108, 110, 106, 104],
        "low":    [98, 100, 99, 103, 101, 97, 102, 104, 100, 98],
        "close":  [103, 101, 103, 106, 104, 100, 107, 105, 101, 102],
        "volume": [1000, 1500, 1200, 2000, 800, 1100, 1800, 900, 1400, 1300],
    }, index=dates, dtype=float)
```

Function-scoped. Используется большинством unit-тестов.

### test_registry.py — консистентность

Гарантирует что каждая функция в FUNCTIONS имеет SIGNATURE и DESCRIPTION, и наоборот:

- Нет функций без сигнатур / описаний
- Нет orphan сигнатур / описаний
- Каждая сигнатура начинается с `func_name(`
- `len(FUNCTIONS) == len(SIGNATURES) == len(DESCRIPTIONS)`

### test_tv_match.py — TradingView matching

Использует реальные данные NQ daily (`load_data("NQ", "1d")`, module-scoped) и CSV с референсными значениями из TradingView. Даты выбираются вдали от contract rolls.

```python
def _assert_close(our_val, tv_val, rel_tol, abs_tol=0):
    """Match within relative OR absolute tolerance."""
    diff = abs(our_val - tv_val)
    if abs_tol and diff <= abs_tol:
        return
    if tv_val == 0:
        assert diff <= abs_tol
        return
    pct = diff / abs(tv_val)
    assert pct <= rel_tol

class TestRSIMatch:
    def test_rsi_matches_tradingview(self, indicators, ref_data):
        for date, row in ref_data.iterrows():
            our = indicators["rsi_14"].loc[date.strftime("%Y-%m-%d")]
            _assert_close(our, row["rsi_14"], rel_tol=0.01, abs_tol=0.5)
```

Tolerance: `rel_tol=0.01` (1%) OR `abs_tol=0.5` — из-за разницы в rollover dates. Window-based индикаторы (CCI, StochK, WilliamsR) сходятся точнее, экспоненциальные (RSI) — расходятся через историю.

### Что тестировать для каждого индикатора

1. **TradingView match** — реальные значения из TV на known dates
2. **Границы** — RSI ∈ [0, 100], Stochastic ∈ [0, 100], Williams %R ∈ [-100, 0]
3. **NaN warmup** — RSI(14) первые 13 баров = NaN (Wilder's seed на 14-м)
4. **Edge cases** — all gains (RSI=100), zero-range bars (A/D), zero volume
5. **Пустой DataFrame** — не падает

### Сбор reference data

1. Открыть TradingView, NQ daily chart (SET mode)
2. Добавить индикатор с дефолтными параметрами
3. Выбрать даты вдали от contract rolls (mid-quarter)
4. Записать дату + OHLCV + значение индикатора
5. Сохранить в `tests/functions/reference_data/nq_oscillators_tv.csv`

---

## Добавление новой функции

1. Написать `_func(df, *args)` в подходящем модуле
2. Добавить в `*_FUNCTIONS`, `*_SIGNATURES`, `*_DESCRIPTIONS`
3. Написать unit-тест в `test_{module}.py`
4. Для индикаторов — TradingView match тест (или добавить точки в `nq_oscillators_tv.csv`)
5. `test_registry.py` автоматически проверит консистентность

6. Добавить имя функции в `DISPLAY_GROUPS` в `assistant/tools/reference.py` (группы для промпта)

`__init__.py` подхватит через `**` unpacking, но `reference.py` имеет явный список функций по группам — без добавления туда функция не появится в промпте Claude.

---

## Files

```
barb/functions/__init__.py         — registry: FUNCTIONS, SIGNATURES, DESCRIPTIONS
barb/functions/_smoothing.py       — wilder_smooth() (internal)
barb/functions/{module}.py         — 12 category modules
tests/functions/conftest.py        — shared df fixture
tests/functions/test_{module}.py   — unit tests per module
tests/functions/test_registry.py   — registry consistency
tests/functions/test_tv_match.py   — TradingView matching on real data
```
