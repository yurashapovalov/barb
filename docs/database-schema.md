# Схема базы данных

Supabase (Postgres). Три таблицы, RLS, каскадное удаление.

## Таблицы

### conversations

Одна строка = один чат. Пользователь видит список в сайдбаре, кликает — открывает.

- `id` — uuid, PK, gen_random_uuid()
- `user_id` — uuid, FK → auth.users(id), каскадное удаление
- `title` — text, по умолчанию 'New conversation', фронт ставит из первого сообщения
- `instrument` — text, по умолчанию 'NQ', выбирается пользователем
- `created_at` — timestamptz, now()
- `updated_at` — timestamptz, now(), обновляется автоматически через триггер

Индекс: `(user_id, updated_at desc)` — сайдбар грузит свежие чаты первыми.

### messages

Одна строка = одно сообщение (пользователь или модель). Загружаются при открытии чата.

- `id` — uuid, PK, gen_random_uuid()
- `conversation_id` — uuid, FK → conversations(id), каскадное удаление
- `role` — text, 'user' или 'model'
- `content` — text, текст сообщения
- `data` — jsonb, только у модели. Массив DataBlock[] — результаты запросов для отображения
- `usage` — jsonb, только у модели. Токены + стоимость ответа
- `created_at` — timestamptz, now()

Индекс: `(conversation_id, created_at asc)` — сообщения в хронологическом порядке.

### tool_calls

Лог каждого вызова тула. Не для UI — для анализа и дебага. Привязан к сообщению модели.

- `id` — uuid, PK, gen_random_uuid()
- `message_id` — uuid, FK → messages(id), каскадное удаление
- `tool_name` — text, 'execute_query', 'understand_question', 'get_reference'
- `input` — jsonb, что передали в тул (query dict)
- `output` — jsonb, что тул вернул (результат)
- `error` — text, null если успешно, текст ошибки если нет
- `duration_ms` — int, время выполнения в миллисекундах
- `created_at` — timestamptz, now()

Индекс: `(message_id, created_at asc)` — tool calls в порядке вызова.

## Что хранится в полях

### Сообщение пользователя
```json
{
  "role": "user",
  "content": "Какой был средний дневной диапазон NQ в 2024?",
  "data": null,
  "usage": null
}
```

### Сообщение модели
```json
{
  "role": "model",
  "content": "Средний дневной диапазон NQ в 2024 составил 285 пунктов...",
  "data": [
    {
      "query": {"timeframe": "D", "select": ["range"], "agg": "mean", "session": "RTH"},
      "result": 285.4,
      "rows": null,
      "session": "RTH",
      "timeframe": "D"
    }
  ],
  "usage": {
    "input_tokens": 1200,
    "output_tokens": 350,
    "thinking_tokens": 800,
    "cached_tokens": 0,
    "input_cost": 0.0018,
    "output_cost": 0.00105,
    "thinking_cost": 0.0024,
    "total_cost": 0.00525
  }
}
```

### data — DataBlock[]

Каждый элемент = результат одного tool call. Gemini может сделать 1–5 вызовов за ответ.

- `result` — скаляр (число, строка) или таблица (массив объектов)
- Пример таблицы: `[{"date": "2024-01-02", "range": 312.5}, {"date": "2024-01-03", "range": 278.0}]`
- Большие таблицы (1000+ строк) остаются в JSONB — Postgres нормально держит. Если станет тормозить — вынесем в Storage.

### usage

Хранится в каждом сообщении модели. Суммарная стоимость чата:
```sql
select sum((usage->>'total_cost')::numeric) from messages where conversation_id = ?
```

Суммарная стоимость пользователя:
```sql
select sum((usage->>'total_cost')::numeric)
from messages
where conversation_id in (select id from conversations where user_id = ?)
```

## RLS (Row Level Security)

Пользователь видит только свои данные.

**conversations** — все операции (select, insert, update, delete) фильтруются по `user_id = auth.uid()`.

**messages** — все операции фильтруются по `conversation_id in (select id from conversations where user_id = auth.uid())`. Прямого user_id на messages нет — владение через conversation.

## Что мы НЕ храним

- **Полный запрос/ответ Gemini** — не нужно. Есть вход (message + history) и выход (answer + data + usage + tool_calls).
- **Профили пользователей** — auth.users metadata хватает. Отдельная таблица profiles не нужна.

## Жизненный цикл

1. Открыл приложение → сайдбар грузит чаты (`conversations order by updated_at desc`)
2. Кликнул на чат → грузятся сообщения (`messages order by created_at asc`)
3. Новый чат → insert conversation → insert user message → вызов API → insert model message
4. Существующий чат → insert user message → вызов API → insert model message (updated_at обновляется автоматически)
5. Удалил чат → каскадно удаляются все сообщения
