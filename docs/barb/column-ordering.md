# Column Ordering

Правила формирования и упорядочивания колонок в результатах запросов.

## Разделение timestamp

Исходный `timestamp` разбивается на `date` и `time` в зависимости от таймфрейма:

| Timeframe | Колонки | Формат |
|-----------|---------|--------|
| 1m, 5m, 15m, 30m, 1h, 2h, 4h | `date` + `time` | `2024-03-15`, `09:30` |
| daily, weekly, monthly, quarterly, yearly | только `date` | `2024-03-15` |

Для недельных/месячных/квартальных/годовых `date` — дата конца периода (pandas offsets W, ME, QE, YE).

## Приоритет колонок

Колонки выводятся в фиксированном порядке:

```
1. date        — всегда первая (идентификатор строки)
2. time        — только для intraday таймфреймов
3. group keys  — если есть group_by
4. OHLC        — open, high, low, close (стандартный порядок)
5. volume      — после OHLC
6. calculated  — колонки из map, в порядке объявления
7. remaining   — все остальные
```

## Примеры

### Weekly данные

```json
{"from": "weekly", "map": {"drop_pct": "..."}}
```

Результат:
```
date | open | high | low | close | volume | drop_pct
```

### Intraday данные

```json
{"from": "1h", "period": "2024-03-15"}
```

Результат:
```
date | time | open | high | low | close | volume
```

### Группировка

```json
{"group_by": "dow", "select": "mean(gap)"}
```

Результат:
```
dow | mean_gap
```

Для сгруппированных данных `date`/`time` не выводятся — это агрегаты.

## Реализация

`barb/interpreter.py` → `_prepare_for_output()`:

```python
def _prepare_for_output(df: pd.DataFrame, query: dict) -> pd.DataFrame:
    """Prepare DataFrame for JSON output: split timestamp, order columns."""
```

Вызывается в `_build_response()` перед сериализацией.

## Точность значений

OHLCV колонки (`_PRESERVE_PRECISION`) сохраняют оригинальную точность из данных. Все остальные float колонки (из `map`, `select`, агрегации) округляются до `CALCULATED_PRECISION = 4` знаков после запятой для удаления FP noise.

Обрабатывается в `_serialize_records()` при конвертации DataFrame → JSON.
