# ADR-010: Decomposed tools вместо execute_query

## Контекст

Модель получала один tool `execute_query` с complex JSON (9 optional полей, free-text expressions). Это приводило к системным ошибкам:

- Писала `select: "sum(x) / count() * 100"` — движок не поддерживает выражения в select
- Придумывала несуществующие столбцы — free-text без ограничений
- Путала поля (expression в group_by вместо map)
- Не могла решить задачи требующие промежуточных вычислений (процент от подмножества)

Проблема была на 100% в генерации JSON, не в исполнении. Executor работал корректно когда получал правильный запрос.

## Решение

Заменили `execute_query` + `get_query_reference` на 15 простых tools, работающих с общим Workspace.

Каждый tool делает одну операцию. Параметры максимально ограничены enum-ами. Модель комбинирует tools последовательно (compositional function calling).

### Tools

- Setup (3): `set_session`, `set_timeframe`, `set_period` — enum параметры
- Columns (2): `add_column`, `add_resampled_column` — вычисляемые столбцы
- Transform (3): `filter_rows`, `sort_rows`, `limit_rows` — модификация данных
- Read (5): `count_rows`, `compute_stat`, `count_by_group`, `stat_by_group`, `get_rows` — чтение
- Control (2): `reset_data`, `get_expression_help`

### Workspace

Stateful объект, живёт один chat turn. Каждый tool модифицирует или читает текущий DataFrame.

### Tool Registry

Tools регистрируются с `group` метаданными. Сейчас модель получает все 15 tools. Когда tools станет больше 20 — включаем dynamic tool selection по группам.

## Первые результаты e2e (Flash Lite)

3/7 PASS, 4 WARN. Модель: `gemini-2.5-flash-lite-preview-09-2025`.

### Что работает

- **Inside day breakout** — полная цепочка из 11 tool calls: reset → setup → add_column → filter → sort → limit → get_rows. Именно тот паттерн, ради которого делали decomposed tools. Раньше модель не могла построить такой запрос одним JSON.
- **Пятничный bias** — stat_by_group по дням недели отработал корректно.
- **Gap fade (частично)** — правильно посчитала 47.6% закрытия гэпов > 20 pts (8 tool calls).
- **Knowledge** — без tools, корректно.

### Что не работает

- **ORB** — crash в парсинге Gemini response (`'NoneType' object has no attribute 'parts'`). Баг в chat.py, не в tools.
- **Модель переспрашивает вместо работы** — в сценариях "Сезонность" и "Gap fade follow-up" модель просит подтверждение повторно вместо вызова tools. Проблема промпта.
- **Потеря контекста между turns** — workspace создаётся заново каждый turn. Модель пытается обратиться к колонкам из прошлого turn. Нужен или hint в промпте, или сохранение state.

### Сравнение с execute_query

- execute_query e2e на том же Flash Lite: 3/7 (те же сценарии, разные ошибки)
- Decomposed tools: 3/7, но характер ошибок принципиально другой

С execute_query ошибки были в **генерации JSON** — модель физически не могла написать правильный запрос. С decomposed tools ошибки в **orchestration** — модель знает какие tools есть, но иногда не вызывает их или теряет контекст. Это проще чинить (промпт, примеры).

## Почему это правильное направление

1. **Enum параметры** — модель не может написать несуществующую сессию или функцию
2. **Immediate feedback** — после каждого tool модель видит сколько строк, какие значения. Раньше ошибка видна только после execute_query
3. **Decomposed complexity** — процент подмножества = два count + арифметика, а не `sum(x)/count()` в select
4. **Масштабируемость** — добавить tool = добавить handler + declaration. Группы готовы для dynamic selection

## Что делать дальше

- Починить crash в chat.py (NoneType parts)
- Улучшить промпт: меньше переспрашиваний, примеры follow-up с reset_data
- Протестировать на более сильной модели (Flash, Pro)
- Решить проблему потери контекста между turns

## Полный дизайн

См. [docs/architecture/decomposed-tools.md](../architecture/decomposed-tools.md)
