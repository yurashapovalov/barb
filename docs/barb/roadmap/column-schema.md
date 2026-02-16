# Display Columns: модель решает что показывать

## Проблема

Сейчас модель контролирует что считать (`map`, `where`, `select`), но не контролирует что показывать. Interpreter сам решает — и решает плохо. Результат: 8 заплаток друг на друге.

1. `_prepare_for_output()` создаёт `date` из timestamp — special case
2. Условно создаёт `time` для intraday — ещё один
3. OHLCV всегда включается в вывод — ещё один
4. Промпт: "don't map date()" — заплатка на #1
5. Промпт: "OHLCV always included" — объяснение #3
6. Alias `date → timestamp` в sort — заплатка на #1
7. `_OHLC_COLUMNS`, `_PRESERVE_PRECISION` — параллельные хардкоды
8. Column reorder (map перед OHLCV) — заплатка на ordering

Причина: interpreter пытается угадать что показывать. Не нужно угадывать — нужно спросить модель.

## Решение

Новое поле `columns` в query. Модель говорит какие колонки показать и в каком порядке. Interpreter показывает ровно это. Если модель не прислала `columns` — fallback, показываем всё как сейчас.

```python
def _prepare_for_output(df, query):
    # 1. Create date/time from timestamp
    ...

    # 2. Show what model asked for
    columns = query.get("columns")
    if columns:
        cols = [c for c in columns if c in df.columns]
        if cols:
            return df[cols]

    # Fallback — model didn't send columns (старые запросы, ошибка)
    return df
```

Всё. Нет views, нет дефолтов, нет ALWAYS/DEFAULT списков. Модель решает — interpreter выполняет.

## Примеры

```json
// "покажи данные за март"
{"from": "daily", "period": "2025-03",
 "columns": ["date", "open", "high", "low", "close", "volume"]}

// "покажи торговые дни в январе"
{"from": "daily", "period": "2026-01", "map": {"день": "dayname()"},
 "columns": ["date", "день"]}

// "когда RSI был ниже 30?"
{"from": "daily", "map": {"rsi": "rsi(close,14)"}, "where": "rsi < 30",
 "columns": ["date", "rsi"]}

// "дни с падением >2.5%"
{"from": "daily", "map": {"chg": "change_pct(close,1)"}, "where": "chg <= -2.5",
 "columns": ["date", "close", "chg"]}

// "покажи RSI и цену закрытия"
{"from": "daily", "map": {"rsi": "rsi(close,14)"},
 "columns": ["date", "rsi", "close"]}

// "средний range по дням недели" — group_by, columns не нужен
{"from": "daily", "map": {"r": "range()", "dow": "dayname()"},
 "group_by": "dow", "select": "mean(r)"}

// "какой средний ATR?" — scalar, columns не нужен
{"from": "daily", "map": {"a": "atr()"}, "select": "mean(a)"}

// golden cross — helper column скрыт
{"from": "daily", "period": "2024",
 "map": {"sma50": "sma(close,50)", "sma200": "sma(close,200)",
         "cross": "crossover(sma(close,50), sma(close,200))"},
 "where": "cross",
 "columns": ["date", "close", "sma50", "sma200"]}
```

`columns` применяется только к table результатам. Scalar и grouped результаты управляют своими колонками — `columns` к ним не применяется.

## Что убирается

| Заплатка | После |
|----------|-------|
| `date` special case | Модель включает `date` в `columns` |
| `time` special case | Модель включает `time` в `columns` для intraday |
| OHLCV всегда включается | Модель включает OHLCV когда нужно |
| Промпт: "don't map date()" | Не нужно |
| Промпт: "OHLCV always included" | Не нужно |
| Alias `date → timestamp` в sort | Source mapping в interpreter |
| `_OHLC_COLUMNS` хардкод | Не нужен |
| `_PRESERVE_PRECISION` хардкод | Precision из function meta (шаг 2) |
| Column reorder 30 строк | `columns` определяет порядок |

## Реализация

### Шаг 1: columns ✅

Реализовано:
- `barb/interpreter.py` — `columns` в `_VALID_FIELDS`, projection в `_prepare_for_output()` перед fallback ordering
- `barb/validation.py` — валидация `columns: string[]`
- `assistant/tools/__init__.py` — `columns` в input_schema, output format rules, 5 примеров с `columns`
- `tests/test_interpreter.py` — 10 тестов в `TestColumns`
- Fallback ordering (`_order_columns` логика) сохранён для обратной совместимости

Не убрано (решено сохранить):
- `_OHLC_COLUMNS`, fallback ordering — нужны для запросов без `columns`

### Шаг 2: Function column metadata (будущее)

- `*_COLUMN_META` в модулях функций
- Per-function precision (заменяет `_PRESERVE_PRECISION` и `CALCULATED_PRECISION`)
