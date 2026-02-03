# Fix Response Quality — Stop Dumping Internal Process to User

## Problem

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

### Step 1: Удалить `understand_question`
- Удалить `assistant/tools/understand.py`
- В `assistant/tools/__init__.py`: убрать `import understand`, убрать из `TOOL_DECLARATIONS` и `_HANDLERS`
- Добавить `## Limitations` секцию в `assistant/tools/reference/format.md`

### Step 2: Переписать системный промпт
- В `assistant/prompt.py`: заменить `<instructions>`, `<constraints>`, `<examples>`
- Убрать ссылку на `understand_question`
- Добавить ограничения на формат ответа (no JSON, no process, one sentence confirmation)
- Переписать примеры с коротким подтверждением

### Step 3: Исправить `rows` в data_block
- В `assistant/chat.py` → `_collect_query_data_block`: rows из result, не из metadata

### Step 4: Обновить тесты
- `tests/test_api.py`: убрать/обновить тесты ссылающиеся на `understand_question`
- Проверить что все существующие тесты проходят

### Step 5: Ручная проверка
- Отправить "частота дней когда range > 2x предыдущего дня"
  - Модель подтверждает ОДНИМ предложением
  - После подтверждения: делает запрос, 1-2 предложения комментария
  - Никакого JSON, планов, описания процесса
  - Карточка показывает корректные данные
- Отправить "что такое inside day?"
  - Ответ без tool calls
- Отправить "сравни дневной и недельный range"
  - Модель честно говорит что cross-timeframe не поддерживается, предлагает альтернативу

## Files to change

| File | Change |
|------|--------|
| `assistant/prompt.py` | Rewrite instructions, constraints, examples |
| `assistant/tools/understand.py` | DELETE |
| `assistant/tools/__init__.py` | Remove understand_question |
| `assistant/tools/reference/format.md` | Add ## Limitations section |
| `assistant/chat.py` | Fix `_collect_query_data_block` rows logic |
| `tests/test_api.py` | Update tests |
