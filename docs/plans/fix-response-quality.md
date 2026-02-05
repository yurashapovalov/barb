# Fix Response Quality

## Problems

### 1. Многословность

Модель вываливает пользователю внутреннюю кухню вместо результата:
- Пересказывает вопрос
- Расписывает план по пунктам
- Просит подтверждение стеной текста вместо одного предложения
- Показывает JSON запроса
- Рассуждает вслух о map/where/mean
- Объясняет зачем каждый параметр

**Корневые причины:**
1. Инструкция #3 в промпте: "Explain to the user what you understood. Wait for the user to confirm" — нет ограничения на формат, модель пишет абзацами
2. `understand_question` tool возвращает статический JSON, не анализирует вопрос, его `instructions` field дублирует "explain to user"
3. Примеры в промпте показывают текст ДО tool calls — модель думает надо комментировать процесс
4. `rows` в data_block показывает обработанные строки (4644), а не результат (448)

### 2. Галлюцинация данных

Модель генерирует конкретные даты, цены, время минимума — без вызова инструментов.

Реальный пример (сессия `c4af0fe9`, 17 обменов):
- Из 17 ответов модели **только 3 содержали tool calls** (7 вызовов всего)
- Успешных `execute_query` — **2 штуки**, оба `count()` (вернули 5 и 10)
- Остальные 14 ответов — модель выдумала: конкретные даты 15 дней, цены open/close/low, время минимума с точностью до минуты, диапазоны 12:00-16:50
- Модель писала "выполняю запрос для проверки..." но tool call не делала

**Корневая причина:** нет механизма принуждения. Модель может ответить текстом вместо вызова инструмента, и ничего её не остановит.

### 3. Нет доказательств

Даже когда модель вызывает инструмент — результат непрозрачен. `count()` возвращает `5`, но пользователь не видит какие именно 5 строк. Верить можно только на слово.

Это касается всех агрегаций:
- `count()` → 5, а какие 5 строк?
- `mean(range)` → 245.3, а range каждого дня какой?
- `max(volume)` → 180000, а когда это было?
- `group_by: weekday, select: mean(range)` → таблица по дням недели, а на основе каких данных?

Интерпретер знает эти строки (они есть в `df` после шага `where`), но при агрегации выбрасывает их.

**Детальный план решения:** [interpreter-source-rows.md](interpreter-source-rows.md)

## Target Flow

```
User: частота дней когда range > 2x предыдущего дня

Round 1 (tool calls, пользователь не видит):
  → get_query_reference(pattern="filter_count")

Round 1 (ответ пользователю):
  "Посчитаю долю дней где range (high-low) в 2+ раза больше range предыдущего дня, RTH daily. Верно?"

User: да

Round 2 (tool calls):
  → execute_query({...})

Round 2 (ответ пользователю):
  "Около 10% торговых дней — довольно редкое событие, обычно сигнализирует о выходе из зоны сжатия волатильности."
  [карточка: RTH · daily]
```

Если вопрос не поддерживается:
```
User: сравни дневной range с недельным

Round 1 (tool calls):
  → get_query_reference(pattern="simple_stat")

Round 1 (ответ):
  "Cross-timeframe сравнение пока не поддерживается. Могу посчитать средний дневной range и средний недельный отдельно — сравнишь сам. Сделать?"
```

## Решение: 3 изменения

### 1. Переписать системный промпт (`assistant/prompt.py`)

**Instructions — было:**
```
1. Call get_query_reference
2. Call understand_question
3. Explain what you understood. Wait for confirm.
4. After confirmation, call execute_query.
5. Commentary about result.
6. On error, fix and retry.
7. Knowledge questions — answer directly.
```

**Instructions — стало:**
```
1. Call get_query_reference with the matching pattern to get the format, examples, and engine limitations.
2. In ONE sentence, tell the user what you will compute. Wait for confirmation.
   - If the question requires unsupported capabilities, say so honestly and suggest the closest alternative.
3. After confirmation, call execute_query with the Barb Script query JSON.
4. The raw data (numbers, tables) is shown to the user automatically by the system. Do not repeat numbers.
   Your job is commentary: what the result means in trading terms, what's typical, what stands out (1-2 sentences).
   Only use facts from the query result — never calculate new numbers from memory.
5. On error, read the error message, fix the query, retry once.
6. For knowledge questions (e.g. "what is an inside day?"), answer directly without queries.
```

**Constraints — добавить:**
```
- Never show JSON queries to the user — the system handles visualization.
- Never describe your internal process (which tools you call, what steps you take).
- Never list steps or plans — just do it.
- The confirmation step (#2) must be ONE sentence, not a paragraph.
- Never state specific prices, dates, counts, or statistics unless they come from an execute_query result in the current conversation turn. If you need data, call the tool.
- If the user asks a follow-up that requires different data (e.g. specific dates after a count, or intraday detail after daily), you MUST call execute_query again — do not extrapolate or invent data from previous results.
```

**Examples — переписать:**

Убрать текст ДО tool calls. Показать одно предложение подтверждения, потом результат:
```
Example 1 — scalar result:

User: What is the average daily range for NQ?
[calls get_query_reference(pattern="simple_stat")]
Assistant: Average daily range across all RTH data. Go?
User: yes
[calls execute_query]
Assistant: Solid baseline for daily volatility. Useful when sizing stops or estimating intraday move potential.

Example 2 — filtered count:

User: How many inside days were there in 2024?
[calls get_query_reference(pattern="filter_count")]
Assistant: Count inside days (high < prev high, low > prev low) in 2024 RTH. Go?
User: yes
[calls execute_query]
Assistant: About 9% of trading days — fairly typical for NQ. Inside days often signal consolidation before a directional move.

Example 3 — unsupported question:

User: Compare daily range with weekly range
[calls get_query_reference(pattern="simple_stat")]
Assistant: Cross-timeframe comparison isn't supported yet. I can compute average daily range and average weekly range separately — you compare. Want that?
```

### 2. Удалить `understand_question`, перенести limitations в reference

**Почему удалить:** Не анализирует вопрос. Возвращает статический JSON. Параметр `question` игнорируется. Дублирует capabilities из `get_query_reference`. Его `instructions` усиливает многословие.

**Куда перенести:** Добавить секцию `## Limitations` в `assistant/tools/reference/format.md`:
```markdown
## Limitations
- No cross-timeframe queries (e.g. comparing daily values with weekly in one query)
- No subqueries or nested queries
- No JOINs or multiple data sources
- No loops or arbitrary code
```

Capabilities уже есть в format.md (список функций, pipeline, expressions). Limitations — единственное что отсутствует. 4 строки.

Когда добавляются новые возможности (бэктесты, индикаторы) — обновляем format.md и добавляем pattern. Limitations уменьшаются. Промпт не растёт.

**Files:**
- `assistant/tools/understand.py` — DELETE
- `assistant/tools/__init__.py` — убрать из `TOOL_DECLARATIONS` и `_HANDLERS`
- `assistant/tools/reference/format.md` — добавить `## Limitations`

### 3. Исправить `rows` в data_block (`assistant/chat.py`)

**Проблема:** `_collect_query_data_block` берёт `rows` из `metadata.rows` — это количество обработанных строк (4644), не результат. Для скалярного count()=448 карточка показывает 4644.

**Исправление:**
```python
result = parsed.get("result")
if isinstance(result, list):
    rows = len(result)       # table — количество строк результата
elif result is not None:
    rows = None              # scalar — нет row count
else:
    rows = None
```

## План реализации

### Phase 1: Source rows (evidence)

Детальный план: [interpreter-source-rows.md](interpreter-source-rows.md)

1. `barb/interpreter.py` — сохранять отфильтрованные строки до агрегации, добавить `source_rows` и `source_row_count` в response
2. `tests/test_interpreter.py` — тесты на source_rows (scalar, group_by, no select, limit)
3. `assistant/tools/__init__.py` — `run_tool` возвращает `(str, dict | None)` вместо `str`
4. `assistant/tools/execute.py` — возвращать `(json_str, raw_result)`, добавить `source_row_count` в JSON для модели
5. `assistant/chat.py` — передавать raw_result в `_collect_query_data_block`, включать source_rows в data_block; исправить rows (из result, не из metadata)
6. Прогнать все тесты

### Phase 2: Промпт и understand_question

1. Удалить `assistant/tools/understand.py`
2. В `assistant/tools/__init__.py`: убрать из `TOOL_DECLARATIONS` и `_HANDLERS`
3. Добавить `## Limitations` секцию в `assistant/tools/reference/format.md`
4. В `assistant/prompt.py`: переписать `<instructions>`, `<constraints>`, `<examples>`
   - Убрать ссылку на `understand_question`
   - Добавить constraints: no JSON, no process, one sentence confirmation, no data without tool call, no extrapolation
   - Переписать примеры с коротким подтверждением
5. Обновить тесты (`tests/test_api.py`) — убрать ссылки на `understand_question`

### Phase 3: Ручная проверка

- Отправить "частота дней когда range > 2x предыдущего дня"
  - Модель подтверждает ОДНИМ предложением
  - После подтверждения: делает запрос, 1-2 предложения комментария
  - Никакого JSON, планов, описания процесса
  - Карточка показывает корректные данные + source rows доступны
- Отправить "покажи эти дни" (follow-up)
  - Модель вызывает execute_query заново, а не выдумывает данные
- Отправить "что такое inside day?"
  - Ответ без tool calls
- Отправить "сравни дневной и недельный range"
  - Модель честно говорит что cross-timeframe не поддерживается, предлагает альтернативу

## Files to change

| File | Phase | Change |
|------|-------|--------|
| `barb/interpreter.py` | 1 | Add source_rows to execute() and _build_response() |
| `tests/test_interpreter.py` | 1 | Add TestSourceRows tests |
| `assistant/tools/__init__.py` | 1+2 | run_tool returns (str, dict), remove understand_question |
| `assistant/tools/execute.py` | 1 | Return (json_str, raw_result), add source_row_count |
| `assistant/chat.py` | 1 | Pass raw_result to data_block, fix rows logic |
| `assistant/tools/understand.py` | 2 | DELETE |
| `assistant/tools/reference/format.md` | 2 | Add ## Limitations section |
| `assistant/prompt.py` | 2 | Rewrite instructions, constraints, examples |
| `tests/test_api.py` | 2 | Remove understand_question references |
