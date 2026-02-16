# Query Engine (barb/)

Ядро системы. Принимает JSON-запрос, выполняет по шагам, возвращает результат.

## Как работает

Запрос — плоский JSON. Каждое поле — шаг пайплайна. Порядок выполнения фиксированный, не зависит от порядка полей в JSON.

```
Входные данные (DataFrame — дневной или минутный)
    ↓
1. session    — фильтр по торговой сессии (RTH, ETH)
2. period     — фильтр по периоду (YYYY, YYYY-MM, YYYY-MM-DD, start:end где каждая часть любого формата, last_year, last_month, last_week)
3. from       — ресемплинг таймфрейма (1m, 5m, 15m, 30m, 1h, 2h, 4h, daily, weekly, monthly, quarterly, yearly)
4. map        — вычисляемые колонки {"name": "expression"}
5. where      — фильтр строк по условию (expression)
6. group_by   — группировка (по колонке из map)
7. select     — агрегация ("count()", "mean(col)", ["sum(x)", "max(y)"])
8. sort       — сортировка ("column desc" или "column asc", по имени колонки из map, не выражению)
9. limit      — ограничение количества строк
    ↓
Результат (summary для модели + table для UI)
```

## Модули

### interpreter.py
Оркестратор. `execute(query, df, sessions)` прогоняет по 9 шагам, возвращает dict с:
- `summary` — компактный результат для модели (зависит от типа, см. ниже)
- `table` — JSON-сериализованные строки для UI (или None для скаляров/dict)
- `source_rows` — исходные строки до агрегации (для прозрачности)
- `source_row_count` — количество исходных строк
- `metadata` — rows, session, from, warnings
- `query` — исходный запрос
- `chart` — hint для фронтенда (`{category, value}`, только для grouped DataFrame результатов; ключ отсутствует в scalar/dict ответах)

Типы summary:
- **table**: `{type, rows, columns, stats:{col:{min,max,mean}}, first:{date,..}, last:{date,..}}`
- **grouped**: table + `{by, min_row, max_row}`
- **scalar**: `{type: "scalar", value, rows_scanned}`
- **dict**: `{type: "dict", values, rows_scanned}`

Валидирует входные данные — неизвестные поля, невалидные таймфреймы, невалидный limit, некорректный map.

### validation.py
Пре-валидация выражений до запуска пайплайна. Без DataFrame — чистый AST-анализ. Проверяет:
- Синтаксис всех выражений (map, where, select)
- Неизвестные функции
- Неподдерживаемые операторы и вызовы методов (`a.upper()` — запрещено)
- `=` вместо `==` (частая ошибка LLM)
- Функции в `group_by` (LLM иногда пишет `group_by: "dayofweek()"` вместо создания колонки в map)
- Формат агрегатных выражений в group_by контексте (должно быть `func(col)` или `count()`)

Собирает все ошибки разом — `ValidationError(errors: list[dict])`.

### expressions.py
Парсер и вычислитель выражений. Безопасный — никакого eval/exec. Строит AST через `ast.parse()`, вычисляет рекурсивно на DataFrame. Поддерживает:
- Арифметику: `+`, `-`, `*`, `/`
- Сравнения: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Булеву логику: `and`, `or`, `not`
- Membership: `in [1, 2, 3]`, `not in [4, 5]`
- Функции: `prev()`, `rolling_mean()`, `dayofweek()`, etc.
- Автоконвертация дат: `date() >= '2024-03-15'` (строки автоматически парсятся в `datetime.date`)

### functions/ (package)
Реестр 106 функций в 12 модулях. Каждый модуль экспортирует `*_FUNCTIONS`, `*_SIGNATURES`, `*_DESCRIPTIONS`. `__init__.py` объединяет в `FUNCTIONS`, `SIGNATURES`, `DESCRIPTIONS`.

Категории:
- **core** (6) — `abs`, `log`, `sqrt`, `sign`, `round`, `if`
- **lag** (2) — `prev`, `next`
- **window** (12) — `sma`, `ema`, `wma`, `hma`, `rma`, `vwma`, `rolling_mean`, `rolling_sum`, `rolling_max`, `rolling_min`, `rolling_std`, `rolling_count`
- **cumulative** (3) — `cumsum`, `cummax`, `cummin`
- **pattern** (8) — `streak`, `bars_since`, `rank`, `rising`, `falling`, `valuewhen`, `pivothigh`, `pivotlow`
- **aggregate** (10) — `mean`, `sum`, `count`, `max`, `min`, `std`, `median`, `percentile`, `correlation`, `last`
- **time** (10) — `dayofweek`, `dayname`, `hour`, `minute`, `month`, `year`, `date`, `monthname`, `day`, `quarter`
- **convenience** (19) — `change`, `change_pct`, `gap`, `gap_pct`, `range`, `range_pct`, `body`, `body_pct`, `upper_wick`, `lower_wick`, `midpoint`, `typical_price`, `green`, `red`, `doji`, `inside_bar`, `outside_bar`, `crossover`, `crossunder`
- **oscillators** (8) — `rsi`, `stoch_k`, `stoch_d`, `cci`, `williams_r`, `mfi`, `momentum`, `roc`
- **volatility** (14) — `tr`, `atr`, `natr`, `bbands_upper`, `bbands_middle`, `bbands_lower`, `bbands_width`, `bbands_pctb`, `donchian_upper`, `donchian_lower`, `kc_upper`, `kc_middle`, `kc_lower`, `kc_width`
- **trend** (9) — `macd`, `macd_signal`, `macd_hist`, `adx`, `plus_di`, `minus_di`, `sar`, `supertrend`, `supertrend_dir`
- **volume** (5) — `obv`, `ad_line`, `vwap_day`, `volume_sma`, `volume_ratio`

### data.py
Загрузка Parquet файлов. `load_data(instrument, timeframe="1d", asset_type="futures")`. Два набора: `data/1d/futures/{symbol}.parquet` (дневные) и `data/1m/futures/{symbol}.parquet` (минутные). Кэшируется через `@lru_cache`. Возвращает DataFrame с DatetimeIndex и колонками [open, high, low, close, volume].

## Пример

Запрос: "дни когда цена упала на 2.5% и более за 2024"

```json
{
  "session": "RTH",
  "period": "2024",
  "from": "daily",
  "map": {"change_pct": "(close - prev(close)) / prev(close) * 100"},
  "where": "change_pct <= -2.5",
  "sort": "change_pct asc"
}
```

Результат:
- summary: `{type: "table", rows: 6, columns: [...], stats: {change_pct: {min: -3.6423, max: -2.6643, mean: -3.152}}, first: {date: "2024-12-18", change_pct: -3.6423}, last: {date: "2024-09-06", change_pct: -2.6643}}`
- table: 6 строк с датами и данными
- source_rows: null (нет агрегации)
- chart: null (нет group_by)
