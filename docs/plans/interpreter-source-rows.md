# Interpreter: Source Rows (Evidence)

## Problem

Интерпретер теряет исходные строки при агрегации.

Pipeline: session → period → from → map → where → **group_by → select** → sort → limit

После шага `where` (строка 101 в `interpreter.py`) в `df` лежат конкретные отфильтрованные строки. Когда есть `select`, шаги 6-7 схлопывают их:

- `count()` → число 5, строки потеряны
- `mean(range)` → число 245.3, строки потеряны
- `max(volume)` → число 180000, строки потеряны
- `group_by: weekday, select: mean(range)` → таблица 5 строк, исходные ~1200 строк потеряны

Пользователь получает результат без доказательства. Модель тоже — и начинает выдумывать данные, когда пользователь просит детали (конкретные даты, цены, время).

Реальный пример из сессии `c4af0fe9`:
1. Модель выполнила `count()` → 5 и 10
2. Пользователь попросил "покажи эти дни"
3. Модель выдала 15 конкретных дат с ценами — **без единого tool call** — всё выдумано

Если бы рядом со счётчиком были строки-источники, модель имела бы данные, а пользователь — доказательство.

## Solution

Одно изменение в интерпретере: сохранять отфильтрованные строки (`source_rows`) рядом с агрегированным результатом.

### Текущий response format

```python
# Scalar (select без group_by)
{"result": 5, "metadata": {...}, "table": None}

# Table (group_by + select)
{"result": [{weekday: 0, mean_range: 230}, ...], "metadata": {...}, "table": [{...}]}

# Rows (без select)
{"result": [{date, open, high, low, close, volume}, ...], "metadata": {...}, "table": [{...}]}
```

### Новый response format

```python
# Scalar — добавляется source_rows
{"result": 5, "metadata": {...}, "table": None, "source_rows": [{date, open, close, ...}, ...5 rows]}

# Table (group_by) — добавляется source_rows
{"result": [{weekday: 0, mean_range: 230}, ...], "table": [{...}], "source_rows": [{date, open, close, range, weekday, ...}, ...1200 rows]}

# Rows (без select) — source_rows == result, не дублируем
{"result": [{...}], "table": [{...}], "source_rows": None}
```

### Когда source_rows есть и когда нет

| Тип запроса | result | source_rows |
|---|---|---|
| Без select (возврат строк) | table | `None` — result уже содержит строки |
| select без group_by (scalar) | scalar | Строки после where, до select |
| group_by + select | grouped table | Строки после where, до group_by |

### Лимит source_rows

Source rows может быть много (mean по всем данным = ~1500 daily строк). Ограничиваем:

- **Для ответа модели (tool response):** НЕ включаем source_rows — слишком много токенов. Модель получает `result` + `source_row_count`.
- **Для data_block (SSE → frontend):** Включаем source_rows, лимит 200 строк. Если больше — первые 200 + `source_row_count` для отображения "showing 200 of 1,247".

## Changes

### 1. `barb/interpreter.py` → `execute()`

Сохранить `df` после шага 5 (where), передать в `_build_response`:

```python
# 5. WHERE
if query.get("where"):
    df = _filter_where(df, query["where"])

rows_after_filter = len(df)
source_df = df  # <-- save reference before aggregation

# 6-7. GROUP BY + SELECT
if group_by:
    result_df = _group_aggregate(df, group_by, select)
elif select_raw:
    result_df = _aggregate(df, select)
else:
    result_df = df
    source_df = None  # result IS the rows, no need to duplicate

# ...
return _build_response(result_df, query, rows_after_filter, session_name, timeframe, warnings, source_df)
```

### 2. `barb/interpreter.py` → `_build_response()`

Добавить `source_df` параметр, конвертировать в list of dicts:

```python
SOURCE_ROWS_LIMIT = 200

def _build_response(result, query, rows, session, timeframe, warnings, source_df=None) -> dict:
    metadata = {
        "rows": rows,
        "session": session,
        "from": timeframe,
        "warnings": warnings,
    }

    # Source rows for evidence (when result is aggregated)
    source_rows = None
    source_row_count = None
    if source_df is not None and isinstance(source_df, pd.DataFrame) and not source_df.empty:
        source_row_count = len(source_df)
        limited = source_df.head(SOURCE_ROWS_LIMIT)
        source_rows = limited.reset_index().to_dict("records")

    if isinstance(result, pd.DataFrame):
        table = result.reset_index().to_dict("records")
        return {
            "result": table,
            "metadata": metadata,
            "table": table,
            "query": query,
            "source_rows": source_rows,
            "source_row_count": source_row_count,
        }

    if isinstance(result, dict):
        return {
            "result": result,
            "metadata": metadata,
            "table": None,
            "query": query,
            "source_rows": source_rows,
            "source_row_count": source_row_count,
        }

    # Scalar
    if hasattr(result, "item"):
        result = result.item()

    return {
        "result": result,
        "metadata": metadata,
        "table": None,
        "query": query,
        "source_rows": source_rows,
        "source_row_count": source_row_count,
    }
```

### 3. `assistant/tools/execute.py` → `run()`

Модели отдаём `source_row_count`, но НЕ отдаём `source_rows` (экономим токены):

```python
return json.dumps({
    "result": result["result"],
    "metadata": result["metadata"],
    "has_table": result["table"] is not None,
    "row_count": len(result["table"]) if result["table"] else None,
    "source_row_count": result.get("source_row_count"),
}, default=str)
```

### 4. `assistant/chat.py` → `_collect_query_data_block()`

Data block для фронтенда включает source_rows:

```python
def _collect_query_data_block(args: dict, tool_result: str, raw_result: dict | None = None) -> dict | None:
    try:
        parsed = json.loads(tool_result)
    except (json.JSONDecodeError, TypeError):
        return None

    if "error" in parsed:
        return None

    result = parsed.get("result")
    if isinstance(result, list):
        rows = len(result)
    elif result is not None:
        rows = None
    else:
        rows = None

    block = {
        "query": args["query"] if "query" in args else args,
        "result": result,
        "rows": rows,
        "session": parsed.get("metadata", {}).get("session"),
        "timeframe": parsed.get("metadata", {}).get("from"),
    }

    # Source rows from interpreter (not from parsed tool_result — too large for JSON)
    if raw_result:
        block["source_rows"] = raw_result.get("source_rows")
        block["source_row_count"] = raw_result.get("source_row_count")

    return block
```

Для этого `chat.py` должен передать `raw_result` из интерпретера в `_collect_query_data_block`. Сейчас `run_tool` возвращает JSON string. Варианты:

**Вариант A:** `run_tool` возвращает tuple `(json_string, raw_dict)`:
- Плюс: чисто, без повторного парсинга
- Минус: меняет сигнатуру run_tool

**Вариант B:** `execute.py` включает source_rows в JSON, `chat.py` достаёт их и удаляет перед отправкой модели:
- Плюс: run_tool сигнатура не меняется
- Минус: гоняем большой JSON туда-сюда

**Рекомендация: Вариант A.** Меняем `run_tool` → возвращает `(str, dict | None)`. Для understand и reference — `(str, None)`. Для execute — `(str, raw_result)`.

### 5. Frontend (`DataPanel`)

Source rows отображаются как таблица-доказательство под основным результатом:

- Scalar: карточка показывает число, DataPanel показывает source_rows таблицу
- Grouped table: карточка показывает сгруппированную таблицу, DataPanel показывает исходные строки
- Rows (без select): карточка = таблица, DataPanel = та же таблица (source_rows = null)

Фронтенд уже умеет рендерить таблицы в DataPanel. Нужно только переключать между result и source_rows.

## What doesn't change

- `barb/expressions.py` — без изменений
- `barb/functions.py` — без изменений
- `barb/validation.py` — без изменений
- Pipeline порядок (session → period → from → map → where → group_by → select → sort → limit) — без изменений
- Формат запросов (JSON query) — без изменений
- Существующие тесты — проходят (новое поле additive)

## Test plan

### Unit tests (`tests/test_interpreter.py`)

Новые тесты:

```python
class TestSourceRows:
    def test_scalar_has_source_rows(self, nq_minute_slice, sessions):
        """count() returns scalar + source rows."""
        result = execute({
            "session": "RTH", "from": "daily",
            "where": "close > open",
            "select": "count()",
        }, nq_minute_slice, sessions)
        assert isinstance(result["result"], (int, float))
        assert result["source_rows"] is not None
        assert len(result["source_rows"]) == result["result"]  # count matches rows

    def test_mean_has_source_rows(self, nq_minute_slice, sessions):
        """mean() returns scalar + all filtered rows."""
        result = execute({
            "session": "RTH", "from": "daily",
            "map": {"range": "high - low"},
            "select": "mean(range)",
        }, nq_minute_slice, sessions)
        assert result["source_rows"] is not None
        assert result["source_row_count"] > 0

    def test_group_by_has_source_rows(self, nq_minute_slice, sessions):
        """group_by returns grouped table + pre-grouped source rows."""
        result = execute({
            "session": "RTH", "from": "daily",
            "map": {"weekday": "dayofweek()"},
            "group_by": "weekday",
            "select": "mean(close)",
        }, nq_minute_slice, sessions)
        assert result["table"] is not None
        assert result["source_rows"] is not None
        assert result["source_row_count"] > len(result["table"])

    def test_no_select_no_source_rows(self, nq_minute_slice, sessions):
        """Without select, result IS the rows — source_rows is None."""
        result = execute({
            "session": "RTH", "from": "daily",
            "where": "close > open",
        }, nq_minute_slice, sessions)
        assert result["source_rows"] is None
        assert isinstance(result["result"], list)

    def test_source_rows_limited(self, nq_minute_slice, sessions):
        """Source rows capped at SOURCE_ROWS_LIMIT."""
        result = execute({
            "session": "RTH", "from": "daily",
            "select": "count()",
        }, nq_minute_slice, sessions)
        assert len(result["source_rows"]) <= 200
        assert result["source_row_count"] == result["result"]
```

### Existing tests

Все существующие тесты (`test_interpreter.py`, `test_expressions.py`, `test_functions.py`, `test_validation.py`) должны проходить без изменений. Новое поле `source_rows` — additive, не ломает существующий формат.

## Implementation order

1. `barb/interpreter.py` — добавить source_rows в execute() и _build_response()
2. `tests/test_interpreter.py` — добавить TestSourceRows
3. `assistant/tools/__init__.py` — run_tool возвращает (str, dict | None)
4. `assistant/tools/execute.py` — возвращать (json_str, raw_result)
5. `assistant/chat.py` — передавать raw_result в _collect_query_data_block
6. Прогнать все тесты
