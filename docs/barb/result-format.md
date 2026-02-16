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
Interpreter              Tool (run_query)          Chat (chat_stream)        API → UI
     │                          │                         │                      │
     │  {summary, table,        │  model_response         │  SSE: text_delta     │
     │   source_rows,           │  (compact string) ────► │   + data_block ────► │
     │   source_row_count,      │  table/source_rows      │  {tool, input,       │
     │   chart*, metadata,      │  chart                  │   result, rows,      │
     │   query}                 │                         │   title, chart}      │
     │                          │                         │                      │
     │                          │                         │  SSE: done           │
     │                          │                         │  {answer, usage,     │
     │                          │                         │   tool_calls, data}  │
```

## Структура ответа интерпретатора

`barb/interpreter.py` → `execute()` → `_build_response()`:

### DataFrame result (table или grouped)

```python
{
    "summary": {
        "type": "table",           # или "grouped"
        "rows": 13,
        "columns": ["open", "high", "low", "close", "volume", "change_pct"],
        "stats": {"change_pct": {"min": -5.06, "max": -2.51, "mean": -3.27}},
        "first": {"date": "2024-08-05", "change_pct": -5.06},
        "last": {"date": "2024-12-18", "change_pct": -2.51},
        # grouped adds:
        "by": "dow",
        "min_row": {"dow": "Fri", "mean_gap": 32.1},
        "max_row": {"dow": "Mon", "mean_gap": 89.5},
    },
    "table": [...],               # полные данные для UI
    "source_rows": [...],         # строки до агрегации (если select)
    "source_row_count": 80,       # сколько строк участвовало
    "chart": {"category": "dow", "value": "mean_gap"},  # только grouped (None для table; отсутствует для scalar/dict)
    "metadata": {"rows": 80, "session": "RTH", "from": "daily", "warnings": []},
    "query": {...}
}
```

### Scalar result

```python
{
    "summary": {"type": "scalar", "value": 65, "rows_scanned": 500},
    "table": None,
    "source_rows": [...],         # строки до агрегации
    "source_row_count": 500,
    "metadata": {...}, "query": {...}
}
```

### Dict result (multiple aggregates)

```python
{
    "summary": {"type": "dict", "values": {"count": 80, "mean": 67.3}, "rows_scanned": 500},
    "table": None,
    "source_rows": [...],         # строки до агрегации
    "source_row_count": 500,
    "metadata": {...}, "query": {...}
}
```

## Tool layer: run_query()

`assistant/tools/__init__.py` → `run_query()` → bridges interpreter and chat:

```python
{
    "model_response": "Result: 13 rows\n  change_pct: min=-5.06, max=-2.51, mean=-3.27",
    "table": [...],           # for UI
    "source_rows": [...],     # evidence for aggregations
    "source_row_count": 80,
    "chart": {...}            # chart hints
}
```

### Форматирование для модели

`_format_summary_for_model()`:

| Тип | Формат для модели |
|-----|-------------------|
| scalar | `Result: 80 (from 500 rows)` |
| dict | `Result: count=80, mean=67.3, max=156.2` |
| table | `Result: 13 rows\n  change_pct: min=-5.06, max=-2.51, mean=-3.27\n  first: date=2024-08-05, change_pct=-5.06\n  last: date=2024-12-18, change_pct=-2.51` |
| grouped | `Result: 5 groups by dow\n  min: dow=Fri, mean_gap=32.1\n  max: dow=Mon, mean_gap=89.5` |

## Типы результатов

| select | group_by | Тип | Пример |
|--------|----------|-----|--------|
| - | - | table | "покажи все дни где gap > 50" |
| scalar | - | scalar | "сколько дней где gap > 50" |
| [list] | - | dict | "покажи count, mean, max" |
| любой | ✓ | grouped | "средний gap по дням недели" |

## source_rows

Предоставляет "доказательство" откуда взялся результат. Заполняется когда `select` присутствует в запросе (`has_aggregation = True`):

| Тип результата | source_rows | Причина |
|----------------|-------------|---------|
| scalar | ДА | Показывает строки которые агрегировались |
| dict | ДА | Показывает строки которые агрегировались |
| grouped (с explicit select) | ДА | Показывает строки до группировки |
| grouped (без select, auto count) | НЕТ | has_aggregation = False |
| table (без select) | НЕТ | table = source, дублирование не нужно |

## Stats — какие колонки

Статистика считается для колонок из `map` + колонки из `sort`:

```python
summary_columns = set(query.get("map", {}).keys())
if query.get("sort"):
    sort_col = query["sort"].split()[0]
    summary_columns.add(sort_col)
```

Stats включает `min`, `max`, `mean` для каждой числовой колонки.

## First/Last

Для table-типа: первая и последняя строка с колонками `["date", "time"] + map_columns`. Только колонки которые реально существуют в serialized output. `last` не включается если всего 1 строка.

## Chart hints

Только для grouped результатов: `{"category": group_by_column, "value": first_aggregate_column}`. UI использует для рендера bar chart.

## Примеры

| Вопрос | summary (модель) | table/source (UI) |
|--------|------------------|-------------------|
| "сколько inside days?" | `{type: scalar, value: 65, rows_scanned: 500}` | 500 строк в source_rows (до агрегации) |
| "средний gap по dow" | `{type: grouped, rows: 5, by: "dow", min_row: {...}, max_row: {...}}` | 5 строк в table |
| "дни где упало >2.5%" | `{type: table, rows: 13, stats: {...}, first: {...}, last: {...}}` | 13 строк в table |
