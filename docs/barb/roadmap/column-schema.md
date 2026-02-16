# Column Schema: единая модель колонок

## Проблема

Текущая система — заплатки поверх отсутствующей модели:

1. `_prepare_for_output()` создаёт `date` из timestamp — special case
2. Условно создаёт `time` для intraday — ещё один
3. OHLCV всегда включается в вывод — ещё один
4. Промпт: "don't map date()" — заплатка на #1
5. Промпт: "OHLCV always included" — объяснение #3
6. Alias `date → timestamp` в sort — заплатка на #1
7. `_OHLC_COLUMNS`, `_PRESERVE_PRECISION` — параллельные хардкоды
8. Column reorder (map перед OHLCV) — заплатка на ordering

Каждый баг → точечный фикс → новый баг. Причина: нет модели колонок.

## Данные провайдера ≠ наши колонки

Parquet от провайдера: `timestamp | open | high | low | close | volume`.

Это источник, не наши колонки. Мы берём оттуда что нужно и показываем как нужно. `open` — не "raw column из parquet", а "цена открытия" которую мы решили показывать. `close` и `rsi(close, 14)` — обе наши колонки.

`date` и `dayname()` — одна природа. Обе из timestamp. Разница — правило включения.

## Полный словарь

Система знает всё что может показать:

| Колонки | Примеры | Кол-во |
|---------|---------|--------|
| Из данных провайдера | open, high, low, close, volume | 5 |
| Из функций | rsi, atr, sma, date, dayname, change_pct, gap, range... | 106 |
| Из агрегаций | count, mean, sum, min, max, std, median | 10 |

Всё известно на этапе сборки. Каждая функция — определение колонки (4-й аспект рядом с FUNCTIONS, SIGNATURES, DESCRIPTIONS).

## Два слоя

### Слой 1: Schema (свойства колонок)

Каждая колонка описывается одинаково:

- **include** — когда показывать: `always`, `default`, `on_request`
- **priority** — порядок в выводе (меньше = раньше)

```python
# barb/columns.py

@dataclass
class ColumnDef:
    name: str
    include: str        # "always" | "default" | "on_request"
    priority: int       # порядок в выводе

COLUMNS = {
    "date":   ColumnDef("date",   include="always",  priority=1),
    "time":   ColumnDef("time",   include="always",  priority=2),
    "open":   ColumnDef("open",   include="default", priority=10),
    "high":   ColumnDef("high",   include="default", priority=11),
    "low":    ColumnDef("low",    include="default", priority=12),
    "close":  ColumnDef("close",  include="default", priority=13),
    "volume": ColumnDef("volume", include="default", priority=14),
}

MAP_COLUMN_PRIORITY = 5

# Derived
DEFAULT_COLUMNS = [c.name for c in COLUMNS.values() if c.include == "default"]
ALWAYS_COLUMNS = [c.name for c in COLUMNS.values() if c.include == "always"]
```

`time` — `include: "always"`, но interpreter включает его только для intraday timeframes. Это условие выполнения, не свойство схемы (как `date` включается всегда, но создаётся только если есть timestamp index).

Precision, source mapping (date → timestamp), creation logic — implementation details в interpreter, не в схеме.

### Слой 2: View logic (interpreter)

Interpreter решает какой view применить на основе запроса. Schema только говорит какие свойства у колонок — interpreter решает что показать.

Три view:

| View | Условие | Колонки |
|------|---------|---------|
| **default** | нет map, нет columns | always + default |
| **computed** | есть map, нет columns | always + map |
| **explicit** | есть columns | ровно то что перечислено |

Применяется **только к table результатам**. Scalar (`select: "mean(r)"`) и grouped (group_by + select) результаты управляют своими колонками — include rules к ним не применяются.

### Алгоритм `_prepare_for_output()`

```python
def _prepare_for_output(df, query):
    # 1. Create date/time from timestamp (implementation detail)
    ...

    # 2. Determine columns to show
    is_grouped = ...  # group_by result
    if is_grouped:
        return order_by_priority(df)

    columns_override = query.get("columns")
    if columns_override:
        # Explicit view
        cols = [c for c in columns_override if c in df.columns]
        return df[cols]

    has_map = bool(query.get("map"))
    if has_map:
        # Computed view — only always + map columns
        map_cols = list(query["map"].keys())
        cols = [c for c in ALWAYS_COLUMNS if c in df.columns]
        cols += [c for c in map_cols if c in df.columns]
        return df[cols]

    # Default view — always + default columns
    cols = [c for c in ALWAYS_COLUMNS if c in df.columns]
    cols += [c for c in DEFAULT_COLUMNS if c in df.columns]
    return df[cols]
```

10 строк вместо текущих 30. Три ветки, каждая очевидна.

## Opt-in вместо opt-out

Сейчас: OHLCV включается всегда, модель не может убрать → шум.

После: модель не "убирает шум", а "добавляет контекст" через `columns`.

### Примеры

```json
// "покажи данные за март" — default view
{"period": "2025-03", "from": "daily"}
// → date | open | high | low | close | volume

// "покажи торговые дни" — computed view
{"period": "2025-03", "from": "daily", "map": {"день": "dayname()"}}
// → date | день

// "покажи RSI" — computed view
{"period": "2025-03", "from": "daily", "map": {"rsi": "rsi(close,14)"}}
// → date | rsi

// "дни с падением >2.5%" — explicit view (модель добавляет close)
{"from": "daily", "map": {"chg": "change_pct(close,1)"}, "where": "chg <= -2.5",
 "columns": ["date", "chg", "close"]}
// → date | chg | close

// "RSI и цену закрытия" — explicit view
{"from": "daily", "map": {"rsi": "rsi(close,14)"}, "columns": ["date", "rsi", "close"]}
// → date | rsi | close
```

## Function column metadata

Каждая функция определяет свойства колонки:

```python
# barb/functions/oscillators.py
OSCILLATOR_COLUMN_META = {
    "rsi": {"precision": 2}, "stoch_k": {"precision": 2},
    "cci": {"precision": 2}, "mfi": {"precision": 2},
}

# barb/functions/time.py
TIME_COLUMN_META = {
    "dayofweek": {"precision": 0}, "dayname": {"precision": None},
    "month": {"precision": 0}, "year": {"precision": 0},
}

# barb/functions/price.py
PRICE_COLUMN_META = {
    "change_pct": {"precision": 2}, "gap_pct": {"precision": 2},
}
```

Expression → root function → lookup precision. Составные выражения → fallback `CALCULATED_PRECISION = 4`.

## Что убирается

| Заплатка | После |
|----------|-------|
| `date` special case | `include: always` |
| `time` special case | `include: always` + intraday check |
| OHLCV всегда включается | `include: default` — только default view |
| Промпт: "don't map date()" | Не нужно |
| Промпт: "OHLCV always included" | Не нужно |
| Alias `date → timestamp` в sort | Source mapping в interpreter |
| `_OHLC_COLUMNS` хардкод | `DEFAULT_COLUMNS` derived |
| `_PRESERVE_PRECISION` хардкод | Precision из function meta |
| Column ordering 30 строк | Priority sort + view logic (10 строк) |
| `CALCULATED_PRECISION = 4` | Per-function precision |

## Реализация

### Шаг 1a: Schema (без изменения поведения)

- `barb/columns.py` — ColumnDef, COLUMNS, derived constants
- interpreter.py — импортирует из columns.py вместо локальных констант
- sort_df() — source mapping из columns.py
- Удалить `_OHLC_COLUMNS`, `_PRESERVE_PRECISION` из interpreter.py
- Тесты проходят, поведение идентичное

### Шаг 1b: View logic + columns (breaking change)

- `_prepare_for_output()` — три view вместо текущей логики
- `barb/validation.py` — валидация `columns: string[]`
- `assistant/tools/__init__.py` — `columns` в input_schema + output format rule
- Промпт — убрать заплатки, добавить правило про `columns`
- E2E тесты — проверить все три view перед деплоем

### Шаг 2: Function column metadata

- `*_COLUMN_META` в модулях функций
- `columns.py` собирает полную схему
- Per-function precision

## Открытые вопросы

1. **group_by**: group results не содержат OHLCV и date — только group keys + aggregates. Include rules не применяются. Нужно убедиться что view logic не ломает этот путь.

2. **Charts**: chart hint ссылается на колонки по имени. Если chart нужен close, а его нет в результате — сломается. Решение: колонки из chart hint автоматически включаются в результат.

3. **Expression → function name**: `"rsi(close, 14)"` → `rsi` → lookup precision. Составные → fallback.

4. **Instrument-dependent precision**: `atr` на NQ ≠ `atr` на ES. Отдельная задача.

5. **Backward compatibility**: default view работает как сейчас. Computed view — breaking change (OHLCV пропадает при наличии map). Тестировать на e2e сценариях.
