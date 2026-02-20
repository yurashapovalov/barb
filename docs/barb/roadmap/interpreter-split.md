# Рефакторинг: разделение interpreter.py

**Status: Done** — ops.py создан, все imports обновлены, QueryError → BarbError, 133 теста проходят.

## Проблема

`barb/interpreter.py` — 746 строк, две роли:

1. **Query engine** — `execute()` + 9-step pipeline + форматирование ответа
2. **Shared утилиты** — `BarbError`, `filter_session`, `filter_period`, `resample`, константы timeframes

Backtest engine, backtest tool, chat.py — все импортируют утилиты из interpreter. Screener будет следующим потребителем. Interpreter станет свалкой.

## Кто что импортирует сейчас

```
barb/backtest/engine.py       → QueryError, resample
assistant/tools/backtest.py   → filter_session, filter_period
assistant/tools/__init__.py   → QueryError, execute
assistant/chat.py             → _INTRADAY_TIMEFRAMES
tests/test_backtest.py        → filter_session, filter_period, QueryError
tests/test_interpreter.py     → QueryError, execute
```

`execute` нужен только query tool. Всё остальное — shared.

## Решение: два модуля

### `barb/ops.py` (~130 строк) — shared data operations

```
BarbError                     — общий error class (сейчас QueryError)
TIMEFRAMES                    — {"1m", "5m", ..., "yearly"}
RESAMPLE_RULES                — {"1m": None, "5m": "5min", ...}
INTRADAY_TIMEFRAMES           — {"1m", "5m", "15m", "30m", "1h", "2h", "4h"}

filter_session(df, session, sessions)  → (df, warning)
filter_period(df, period)              → df
resample(df, timeframe)                → df
```

Приватные зависимости (уходят вместе):
- `_RELATIVE_PERIODS`, `_PERIOD_RE` — используются `filter_period`

Импорты ops.py:
```python
import re
import pandas as pd
```

Ноль barb-зависимостей.

### `barb/interpreter.py` (~620 строк) — query engine

```python
from barb.ops import (
    BarbError,
    TIMEFRAMES,
    INTRADAY_TIMEFRAMES,
    filter_session,
    filter_period,
    resample,
)
```

Остаётся всё query-specific: `execute()`, `_validate()`, `compute_map()`, `filter_where()`, `_group_aggregate()`, `_aggregate()`, `sort_df()`, `_build_response()`, форматирование, сериализация.

Query-only константы:
- `_VALID_FIELDS`, `_OHLC_COLUMNS`, `_PRESERVE_PRECISION`, `CALCULATED_PRECISION`

## `QueryError` → `BarbError`

Сейчас `QueryError` бросается из backtest engine (`"Invalid direction"`, `"Unsupported timeframe"`) и из `filter_period` (`"Invalid period"`). Это не query error — это общая ошибка barb. Раз всё равно обновляем все import paths — переименовать сейчас дешевле всего.

Места для замены:
- `barb/interpreter.py` — ~18 raises (error_type field остаётся строкой, не меняется)
- `barb/backtest/engine.py` — 2 raises
- `assistant/tools/__init__.py` — 1 catch
- `tests/` — ~12 мест

## Обновление импортов

| Файл | Было | Стало |
|------|------|-------|
| `barb/interpreter.py` | `class QueryError` inline | `from barb.ops import BarbError, TIMEFRAMES, ...` |
| `barb/backtest/engine.py` | `from barb.interpreter import QueryError, resample` | `from barb.ops import BarbError, resample` |
| `assistant/tools/backtest.py` | `from barb.interpreter import filter_period, filter_session` | `from barb.ops import filter_period, filter_session` |
| `assistant/tools/__init__.py` | `from barb.interpreter import QueryError, execute` | `from barb.ops import BarbError` + `from barb.interpreter import execute` |
| `assistant/chat.py` | `from barb.interpreter import _INTRADAY_TIMEFRAMES` | `from barb.ops import INTRADAY_TIMEFRAMES` |
| `tests/test_backtest.py` | `from barb.interpreter import ...` | `from barb.ops import ...` |
| `tests/test_interpreter.py` | `from barb.interpreter import QueryError, execute` | `from barb.ops import BarbError` + `from barb.interpreter import execute` |

## Что НЕ меняется

- **Логика** — ни одна строка логики не меняется. Чистый move + rename.
- **`execute()` API** — `execute(query, df, sessions)` остаётся прежним
- **`barb/backtest/engine.py`** — только import path + error name
- **`barb/data.py`**, **фронтенд** — не трогаем
- **Тесты** — остаются в `test_interpreter.py` (тестируют через `execute()`, не напрямую)

## Порядок выполнения

1. Создать `barb/ops.py` — BarbError, constants, filter_session, filter_period, resample
2. Обновить `barb/interpreter.py` — import из ops, удалить перемещённый код, `QueryError` → `BarbError`
3. Обновить `barb/backtest/engine.py` — import + rename
4. Обновить `assistant/` — 3 файла
5. Обновить `tests/` — 2 файла
6. `.venv/bin/pytest tests/test_interpreter.py tests/test_backtest.py -v`
7. `.venv/bin/ruff check barb/ assistant/ tests/`

## Результат

```
barb/
  ops.py             — shared: BarbError, filter/resample, timeframe constants
  interpreter.py     — query engine: execute() + 9-step pipeline
  expressions.py     — AST parser
  functions/         — 106 trading functions
  data.py            — parquet loading
  validation.py      — input validation
  backtest/          — simulation engine
```

Каждый модуль — одна ответственность. Ops — операции над OHLCV данными. Interpreter — JSON queries. Backtest — симуляция. Screener завтра импортирует из ops, не трогая interpreter.

## Риски

Минимальные. Чистый move + rename. Код не меняется, только перемещается. Lint + тесты ловят пропущенные imports мгновенно.
