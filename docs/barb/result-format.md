# Result Format: Model vs UI

Разделение данных между моделью (компактный summary) и UI (полные данные).

## Принцип

```
┌─────────────────────────────────────────────────────────────────┐
│  UI получает:     ПОЛНЫЕ данные (table / source_rows)          │
│  Модель получает: МИНИМУМ для комментария (summary)            │
└─────────────────────────────────────────────────────────────────┘
```

## Поток данных

```
Interpreter                    Tool                      Chat                     API
     │                          │                         │                        │
     │  {                       │                         │                        │
     │    summary: {...},       │                         │                        │
     │    table: [...rows],     │   model_response        │   SSE: data_block      │
     │    source_rows: [...]    │ ──────────────────────► │ ─────────────────────► │  UI
     │  }                       │   (compact string)      │   {table: rows}        │
     │                          │                         │                        │
     │                          │                         │   SSE: done            │
     │                          │                         │ ─────────────────────► │  Supabase
     │                          │                         │   {data: rows}         │
```

## Структура ответа интерпретатора

`barb/interpreter.py` → `execute()` возвращает:

```python
{
    "summary": {
        "type": "table",           # scalar | dict | table | grouped
        "rows": 13,
        "stats": {
            "change_pct": {"min": -5.06, "max": -2.51, "mean": -3.27}
        },
        "first": {"timestamp": "2025-04-08", "change_pct": -5.06},
        "last": {"timestamp": "2024-09-03", "change_pct": -2.51},
    },

    "table": [...],           # полные данные для UI
    "source_rows": [...],     # строки до агрегации (для scalar/dict)
    "source_row_count": 80,   # сколько строк участвовало в расчёте
    "metadata": {...},
    "query": {...}
}
```

## Форматирование для модели

`assistant/tools/__init__.py` → `_format_summary_for_model()`:

| Тип | Формат для модели |
|-----|-------------------|
| scalar | `Result: 80 (from 500 rows)` |
| dict | `Result: count=80, mean=67.3, max=156.2` |
| table | `Result: 13 rows\n  change_pct: min=-5.06, max=-2.51, mean=-3.27` |
| grouped | `Result: 5 groups by dow\n  min: dow=Fri, mean_gap=45` |

## Типы результатов

| select | group_by | Тип | Пример |
|--------|----------|-----|--------|
| - | - | table | "покажи все дни где gap > 50" |
| scalar | - | scalar | "сколько дней где gap > 50" |
| [list] | - | dict | "покажи count, mean, max" |
| любой | ✓ | grouped | "средний gap по дням недели" |

## source_rows

Предоставляет "доказательство" откуда взялся результат:

| Тип результата | source_rows | Причина |
|----------------|-------------|---------|
| scalar/dict | ДА | Показывает строки которые агрегировались |
| grouped | НЕТ | table сам является результатом |
| table | НЕТ | table = source, дублирование не нужно |

## Stats — какие колонки

Статистика считается для колонок из `map` + колонки из `sort`:

```python
stats_columns = set(query.get("map", {}).keys())
if query.get("sort"):
    sort_col = query["sort"].split()[0]
    stats_columns.add(sort_col)
```

## Примеры

| Вопрос | summary (модель) | table/source (UI) |
|--------|------------------|-------------------|
| "сколько inside days?" | `{type: scalar, value: 65}` | 65 строк в source_rows |
| "средний gap по dow" | `{type: grouped, rows: 5, ...}` | 5 строк в table |
| "дни где упало >2.5%" | `{type: table, rows: 13, ...}` | 13 строк в table |
