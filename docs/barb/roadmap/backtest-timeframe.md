# Backtest Timeframe Refactoring

## Проблема

Две проблемы — одна фича, один рефакторинг.

**1. Нет intraday бэктестов.** Engine хардкодит `resample(df, "daily")`. `hour()` и `minute()` всегда 0 на дневных барах. Нельзя тестировать "вход в 10:00" или "шорт на последнем часе". Реальный кейс: "optimal time to enter if SL 50, target 100, breakeven 20 min after entry" — ассистент делает 10 безуспешных попыток.

**2. Engine дублирует query pipeline.** Backtest engine импортирует `filter_session`, `filter_period`, `resample` из interpreter и вызывает их сам. Это работа query engine — подготовка данных. Engine должен заниматься только симуляцией.

## Принцип: разделение тулов

Каждый тул делает одну работу:

| Тул | Ответственность |
|-----|-----------------|
| **Query engine** (`barb/interpreter.py`) | **Данные.** Фильтрация (session, period), ресемплинг (timeframe), трансформации (map, where, group_by). Обслуживает всех — и пользователя (run_query), и другие тулы. |
| **Backtest engine** (`barb/backtest/engine.py`) | **Симуляция.** Получает готовые данные + стратегию → считает сделки, метрики, equity. Не знает откуда данные пришли. |
| **Tool wrappers** (`assistant/tools/`) | **Оркестрация.** Парсят LLM input, вызывают нужные функции в правильном порядке, форматируют output. |

Engine не должен знать про sessions, session, period. Это забота tool wrapper'а, который использует функции interpreter'а для подготовки данных.

## Что меняется

### 1. Разделение ответственности

**Сейчас** — engine делает три работы: подготовку данных + ресемпл + симуляцию:

```
run_backtest_tool()              ← парсит JSON
  └→ run_backtest(df_minute, strategy, sessions, session, period)
       ├→ filter_session()       ← дублирует interpreter
       ├→ filter_period()        ← дублирует interpreter
       ├→ resample("daily")      ← хардкод
       └→ _simulate()            ← уникальная логика
```

**После** — tool wrapper готовит данные, engine только симулирует:

```
run_backtest_tool()
  ├→ filter_session()            ← interpreter (один раз, здесь)
  ├→ filter_period()             ← interpreter (один раз, здесь)
  └→ run_backtest(df_filtered, strategy, timeframe="daily")
       ├→ _build_minute_index()  ← маппинг бар→минутки
       ├→ resample(df, timeframe)
       └→ _simulate()
```

Engine не знает про sessions/session/period. Получает отфильтрованные данные + timeframe.

### 2. `minute_by_date` → `_build_minute_index`

Текущий подход — группировка по дате:

```python
minute_by_date = {d: group for d, group in df.groupby(df.index.date)}
# lookup: minute_by_date[bar_date.date()]
```

Работает только для daily. Для часового бара нужно найти минутки в [10:00, 11:00), не за весь день.

Новый подход — `searchsorted` для O(m log n):

```python
def _build_minute_index(
    minutes: pd.DataFrame, bars: pd.DataFrame
) -> dict[int, pd.DataFrame]:
    """Map bar index → minute DataFrame for exit resolution.

    Uses searchsorted on sorted DatetimeIndex — O(m log n) where
    m = minutes, n = bars. Much faster than naive O(n × m) loop.
    """
    if minutes.empty or bars.empty:
        return {}
    # For each minute, find which bar it belongs to
    indices = bars.index.searchsorted(minutes.index, side="right") - 1
    result = {}
    for i in range(len(bars)):
        mask = indices == i
        if mask.any():
            result[i] = minutes[mask]
    return result
```

Универсально для любого таймфрейма: daily бар → все минутки этого дня, часовой бар 10:00 → минутки 10:00–10:59.

В `_simulate` lookup упрощается:

```python
# Было:
day_key = bar_date.date() if hasattr(bar_date, "date") else bar_date
day_minutes = minute_by_date.get(day_key)

# Стало:
bar_minutes = minute_by_bar.get(i)
```

### 3. Валидация timeframe

Допустимые значения для бэктеста:

```python
_BACKTEST_TIMEFRAMES = {"5m", "15m", "30m", "1h", "2h", "4h", "daily"}
```

Блокируем:
- `1m` — resample = no-op, 500K итераций в _simulate, minute exit resolution бессмысленна (бар = 1 минута)
- `weekly`/`monthly`/`quarterly`/`yearly` — слишком мало баров для бэктеста, exit_bars семантика абсурдна

Валидация в начале `run_backtest()` — raise `QueryError` для недопустимых значений.

### 4. `exit_bars` и `breakeven_bars` семантика

`exit_bars: 5` на daily = 5 дней. На 1h = 5 часов. На 15m = 75 минут.

Это стандартное поведение (TradingView, Backtrader). Документируем в tool description, не меняем логику.

### 5. Производительность

| Timeframe | Баров (1 год) | `_build_minute_index` | `_simulate` |
|-----------|---------------|-----------------------|-------------|
| daily | ~250 | <10ms | <100ms |
| 1h | ~1,750 | <10ms | ~200ms |
| 15m | ~7,000 | <10ms | ~500ms |
| 5m | ~21,000 | <10ms | ~1-2s |

`_build_minute_index` с searchsorted = O(m log n), одинаково быстрый для всех таймфреймов. Bottleneck — `_simulate` (линейный проход по барам + minute exit resolution для открытых позиций).

Не оптимизируем заранее — смотрим на реальную скорость после реализации.

## Файлы и изменения

### `barb/backtest/engine.py`

**Сигнатура:**

```python
# Было:
def run_backtest(df, strategy, sessions, session=None, period=None):

# Стало:
def run_backtest(df, strategy, timeframe="daily"):
```

**Внутри run_backtest:**

```python
# Убрать:
if session:
    df, _ = filter_session(df, session, sessions)
if period:
    df = filter_period(df, period)
minute_by_date = {d: g for d, g in df.groupby(df.index.date)}
daily = resample(df, "daily")

# Заменить на:
if timeframe not in _BACKTEST_TIMEFRAMES:
    raise QueryError(...)
bars = resample(df, timeframe)
minute_by_bar = _build_minute_index(df, bars)
```

**`_simulate`:** `minute_by_date: dict` → `minute_by_bar: dict[int, pd.DataFrame]`. Lookup `minute_by_bar.get(i)` вместо `minute_by_date.get(day_key)`. Два места (entry bar check + position check).

**`_resolve_exit`** и ниже: без изменений — они работают с произвольным DataFrame минуток.

**Импорты:** убрать `filter_period`, `filter_session` (больше не нужны в engine).

### `assistant/tools/backtest.py`

**Tool schema — добавить `"from"`:**

```python
"from": {
    "type": "string",
    "description": "Bar timeframe: daily (default), 1h, 4h, 15m, etc.",
},
```

**Tool description — обновить:**

```
# Убрать:
IMPORTANT: Entry conditions are evaluated on DAILY bars. hour() and minute()
always return 0 — do NOT use time-based entry conditions.

# Заменить на:
Default timeframe is daily. Use "from" field for intraday backtests (1h, 15m, etc.).
exit_bars and breakeven_bars count bars at the chosen timeframe.
```

**`run_backtest_tool()` — data prep здесь:**

```python
def run_backtest_tool(input_data, df_minute, sessions):
    # ... parse strategy ...

    # Data preparation (moved from engine)
    df = df_minute
    session = input_data.get("session")
    period = input_data.get("period")
    timeframe = input_data.get("from", "daily")

    if session:
        df, _ = filter_session(df, session, sessions)
    if period:
        df = filter_period(df, period)

    result = run_backtest(df, strategy, timeframe=timeframe)
```

### `tests/test_backtest.py`

**Синтетические тесты (daily_df):** убрать `empty_sessions` из вызовов. Было: `run_backtest(daily_df, strategy, empty_sessions)` → стало: `run_backtest(daily_df, strategy)`. ~18 вызовов. Фикстура `empty_sessions` удаляется.

**Real NQ тесты:** pre-filter в фикстуре:

```python
@pytest.fixture
def nq_rth(nq_minute_slice, sessions):
    """NQ minute data filtered to RTH."""
    df, _ = filter_session(nq_minute_slice, "RTH", sessions)
    return df

# Было:
result = run_backtest(nq_minute_slice, strategy, sessions, session="RTH")
# Стало:
result = run_backtest(nq_rth, strategy)
```

~6 вызовов. Фикстура `nq_rth` вычисляется один раз.

**Тест period filter:** pre-filter оба варианта:

```python
df_rth, _ = filter_session(df, "RTH", sessions)
r_full = run_backtest(df_rth, strategy)
r_month = run_backtest(filter_period(df_rth, "2024-03"), strategy)
```

**Breakeven/trailing тесты с минутками:** ~5 вызовов. Эти тесты создают свои минутные фикстуры и передают `sessions={}` — убрать sessions, вызов становится `run_backtest(df, strategy)`.

**Всего: ~29 вызовов обновить.** Все ломаются на уровне сигнатуры (TypeError) — никаких тихих поломок.

**Новые тесты:**

```python
class TestIntraday:
    def test_hourly_entry(self, minute_fixture):
        """Entry at specific hour works on hourly bars."""
        # Синтетическая минутная фикстура с известными ценами
        strategy = Strategy(entry="hour() == 10", direction="long", exit_bars=3)
        result = run_backtest(minute_fixture, strategy, timeframe="1h")
        assert result.metrics.total_trades > 0
        # Verify entry is on the NEXT bar after signal (11:00, not 10:00)
        for trade in result.trades:
            assert trade.entry_price == ...  # проверяем конкретную цену

    def test_minute_exit_within_hourly_bar(self, minute_fixture):
        """Minute data resolves exact exit within hourly bars."""
        strategy = Strategy(entry="close > prev(close)", direction="long", take_profit=2)
        result = run_backtest(minute_fixture, strategy, timeframe="1h")
        tp_trades = [t for t in result.trades if t.exit_reason == "take_profit"]
        assert len(tp_trades) > 0
        # Verify exit price = take_profit level, not bar close
        for t in tp_trades:
            assert t.exit_price == pytest.approx(t.entry_price + 2, abs=0.5)

    def test_build_minute_index_boundaries(self):
        """_build_minute_index maps minutes to correct bars."""
        # 3 hourly bars, 180 minutes → each bar gets 60 minutes
        ...

    def test_exit_bars_counts_timeframe_bars(self, minute_fixture):
        """exit_bars=2 on 1h means 2 hours, not 2 days."""
        strategy = Strategy(entry="close > prev(close)", direction="long", exit_bars=2)
        result = run_backtest(minute_fixture, strategy, timeframe="1h")
        for trade in result.trades:
            if trade.exit_reason == "timeout":
                assert trade.bars_held == 2

    def test_invalid_timeframe(self):
        """Unsupported timeframe raises error."""
        strategy = Strategy(entry="close > 100", direction="long")
        with pytest.raises(Exception):
            run_backtest(df, strategy, timeframe="weekly")

    def test_daily_regression(self, daily_df):
        """Daily timeframe gives same results as before refactoring."""
        strategy = Strategy(entry="close > 107", direction="long", exit_bars=1)
        result = run_backtest(daily_df, strategy)  # default timeframe="daily"
        # Same assertions as existing test_basic_long_entry
        assert len(result.trades) > 0
        for trade in result.trades:
            assert trade.direction == "long"
            assert trade.exit_reason == "timeout"
```

### `assistant/chat.py`

Без изменений. `_exec_backtest` передаёт `df_minute` и `sessions` в `run_backtest_tool`, который теперь сам фильтрует.

### `api/main.py`

Без изменений. `POST /api/backtest` вызывает `run_backtest_tool(input_data, df_minute, sessions)` — сигнатура tool wrapper'а не меняется.

**Follow-up:** strategy card пока не показывает поле `from`. Добавить в карточку — отдельная задача после этого рефакторинга.

## Риски

### Что НЕ сломается (нулевой риск)

**Production chat flow.** `assistant/chat.py:_exec_backtest` → `run_backtest_tool(input_data, self.df_minute, self.sessions)`. Сигнатура `run_backtest_tool` не меняется. Внутри — те же функции, тот же порядок (session → period → resample), просто session/period переехали из engine в wrapper. Данные на входе и выходе идентичны.

**API endpoint.** `POST /api/backtest` → `run_backtest_tool(...)`. Тот же вызов.

**E2E тесты.** Проходят через `chat_stream` → `_exec_backtest` → `run_backtest_tool`. Без изменений.

### Что может сломаться (низкий риск, контролируемый)

**1. Смена code path для daily данных.**

Сейчас: синтетические тесты передают daily DataFrame, `minute_by_date` пустой → `_resolve_exit` идёт в `_check_exit_levels`.

После: `_build_minute_index(daily_df, bars)` вернёт по одной строке на бар → `_resolve_exit` пойдёт в `_find_exit_in_minutes` с одной строкой.

**Верифицировано:** `_find_exit_in_minutes` с одной строкой = `_check_exit_levels`. Идентичная логика: trailing update → stop → TP → target. Один и тот же порядок проверок, одни и те же return values. Тип данных тоже идентичен: оба получают `bar["high"]`, `bar["low"]` из pd.Series.

**Митигация:** прогнать все 70 тестов, убедиться что результаты идентичны. Это regression gate — если хоть один тест даёт другой результат, мы ловим баг до мержа.

**Follow-up:** если все тесты проходят, можно убрать `_check_exit_levels` совсем (один path вместо двух). Но это отдельный PR.

**2. Тесты ломаются на уровне сигнатуры (~29 вызовов).**

Все вызовы `run_backtest(df, strategy, sessions, ...)` дадут TypeError — третий позиционный аргумент теперь `timeframe`, не `sessions`. Ни один тест не пройдёт молча с неправильными данными.

**Митигация:** механическая замена. 3 категории:
- `run_backtest(daily_df, strategy, empty_sessions)` → `run_backtest(daily_df, strategy)` (~18)
- `run_backtest(df, strategy, sessions, session="RTH")` → pre-filter + `run_backtest(df_rth, strategy)` (~6)
- `run_backtest(df, strategy, sessions)` (no filter) → `run_backtest(df, strategy)` (~5)

**3. LLM отправляет невалидный timeframe.**

`from: "1m"` — resample no-op, 500K итераций. `from: "weekly"` — 52 бара, бессмысленно.

**Митигация:** whitelist `_BACKTEST_TIMEFRAMES` + QueryError. Также добавить в tool description допустимые значения.

### Чего точно НЕ произойдёт

- **Тихая поломка:** невозможна. Сигнатура engine ломает все тесты явно (TypeError).
- **Разные результаты для daily:** `_find_exit_in_minutes(1 row)` = `_check_exit_levels(bar)`. Верифицировано по коду.
- **Проблемы с production:** `run_backtest_tool` — единственная entry point. Его сигнатура не меняется.

## Порядок работы

1. `engine.py` — новая сигнатура + `_build_minute_index` + валидация + убрать session/period
2. `backtest.py` (tool) — session/period фильтрация + `from` в schema + description
3. `test_backtest.py` — обновить ~29 вызовов + regression тест + новые intraday тесты
4. `.venv/bin/pytest tests/test_backtest.py -v` — все 70+ тестов зелёные
5. `.venv/bin/ruff check barb/backtest/ assistant/tools/backtest.py`
6. E2e — проверить что существующие backtest сценарии проходят

## Чего НЕ делаем

- Убирать `_check_exit_levels` — оставляем, удалим в отдельном PR после верификации
- Оптимизация `_simulate` — сначала измерим на реальных данных
- Поддержка weekly/monthly/1m — блокируем валидацией
- Поле `from` в strategy card — отдельная задача
- Изменение exit_bars семантики — bars = bars на выбранном таймфрейме, как везде
