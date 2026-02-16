# Column Ordering

Какие колонки попадают в результат и в каком порядке.

## Два режима

### 1. Projection — модель указывает `columns`

Модель присылает `"columns": ["date", "close", "chg"]` в запросе. Interpreter показывает ровно эти колонки в указанном порядке. Без дополнений, без OHLCV по умолчанию.

Правило порядка в промпте: `date/time first, then answer columns (from map), then supporting context (close, volume)`. Идентификация → ответ → контекст.

Технически projection применяется ко всем DataFrame результатам (включая grouped). Но для grouped результатов колонки из `columns` обычно не совпадают с реальными (group key + aggregate) → fallback. Промпт говорит: "Omit columns for scalar/grouped results."

### 2. Fallback — модель не прислала `columns`

Если `columns` нет в запросе — обратная совместимость. Колонки выводятся в фиксированном порядке:

```
1. date        — всегда первая
2. time        — только для intraday
3. group keys  — если есть group_by
4. calculated  — колонки из map, в порядке объявления (перед OHLC — derived data важнее сырых свечей)
5. OHLC        — open, high, low, close
6. volume
7. remaining   — все остальные
```

## Разделение timestamp

Перед projection или fallback ordering, `timestamp` разбивается на `date` и `time`:

| Timeframe | Колонки | Формат |
|-----------|---------|--------|
| 1m, 5m, 15m, 30m, 1h, 2h, 4h | `date` + `time` | `2024-03-15`, `09:30` |
| daily, weekly, monthly, quarterly, yearly | только `date` | `2024-03-15` |

Модель пишет `"date"` в `columns` — interpreter знает как его создать из timestamp.

## Примеры

### Projection — фильтр с контекстом

```json
{"from": "daily", "period": "2024:2025",
 "map": {"chg": "change_pct(close, 1)"}, "where": "chg <= -2.5",
 "columns": ["date", "chg", "close"]}
```

Результат: `date | chg | close` — ответ (chg) перед контекстом (close).

### Projection — скрытый helper

```json
{"from": "daily", "period": "2024",
 "map": {"sma50": "sma(close,50)", "sma200": "sma(close,200)",
         "cross": "crossover(sma(close,50),sma(close,200))"},
 "where": "cross",
 "columns": ["date", "close", "sma50", "sma200"]}
```

Результат: `date | close | sma50 | sma200` — `cross` использовался для фильтра, но скрыт.

### Fallback — без columns

```json
{"from": "daily", "map": {"chg": "change_pct(close, 1)"}, "where": "chg <= -2.5"}
```

Результат: `date | chg | open | high | low | close | volume` — fallback ordering.

### Группировка — без columns, fallback

```json
{"group_by": "dow", "select": "mean(gap)"}
```

Результат: `dow | mean_gap` — без `columns`, fallback порядок (group key + aggregate).

## Реализация

`barb/interpreter.py` → `_prepare_for_output()`:

1. Split timestamp → date/time
2. Если `columns` есть → projection (фильтр + порядок по массиву)
3. Иначе → fallback ordering (фиксированный приоритет)

Вызывается в `_build_response()` перед сериализацией. Валидация формата `columns` (должен быть массив строк) — в `barb/validation.py`.

### Сохранение порядка через JSONB

PostgreSQL JSONB не сохраняет порядок ключей. Бэкенд (`assistant/chat.py`) извлекает порядок колонок из сериализованных записей и передаёт как `columns` в data_block. Фронтенд (`data-panel.tsx`) использует `columnOrder ?? Object.keys(rows[0])` — приоритет у `columns` из бэкенда, fallback на порядок ключей для старых данных.

## Точность значений

OHLCV колонки (`_PRESERVE_PRECISION`) сохраняют оригинальную точность из данных. Все остальные float колонки округляются до `CALCULATED_PRECISION = 4` знаков для удаления FP noise.

Обрабатывается в `_serialize_records()` при конвертации DataFrame → JSON.
