# Backend Foundation

Фундамент бэкенда — вещи которые закладываются один раз и работают на протяжении всего проекта.

## 1. Request ID

Каждый запрос получает уникальный ID. Прокидывается через все слои: логи, Supabase, ответ клиенту.

- Генерируется на входе в middleware
- Добавляется в каждую запись лога
- Сохраняется в messages (новая колонка `request_id`)
- Возвращается клиенту в response header `X-Request-Id`
- Если клиент шлёт `X-Request-Id` — используем его (для сквозного трейсинга)

Юзер пишет "у меня ошибка" → даёт request_id → находим весь путь запроса.

## 2. Health Check

Сейчас `/health` всегда возвращает `ok`. Нужно проверять зависимости:

- Supabase: `db.table("conversations").select("id").limit(1).execute()`
- Gemini API: проверка что ключ валидный (кэшированная проверка, не на каждый health check)
- Data: файл `data/NQ.parquet` существует

Если что-то не работает — health check возвращает 503. Docker перезапускает контейнер.

```json
{
  "status": "ok",
  "checks": {
    "supabase": "ok",
    "gemini": "ok",
    "data": "ok"
  }
}
```

## 3. Structured Errors

Единый формат ошибок для всех эндпоинтов:

```json
{
  "error": "Conversation not found",
  "code": "NOT_FOUND",
  "request_id": "abc-123"
}
```

Коды: `VALIDATION_ERROR`, `NOT_FOUND`, `UNAUTHORIZED`, `SERVICE_UNAVAILABLE`, `INTERNAL_ERROR`.

Фронт парсит `code` для логики, `error` для отображения юзеру.

## 4. Контекстная память

Каждая сессия (conversation) — чистый лист. Между сессиями ничего не помним.

### Что хранится в контексте Gemini

Только текст из `messages.content` (role + content). Таблицы (`data`), tool calls и их результаты **не попадают** в контекст. Они сохранены в DB для отображения на фронте, но Gemini их не видит при следующем запросе.

Это значит контекст лёгкий — чистый текст "вопрос → ответ". 20 обменов ≈ 3-5k токенов.

### Стратегия: sliding window + summary

Первые 20 обменов — полная история. После 20 — суммаризируем старое, храним summary в conversation.

```
Gemini получает:
  system_prompt
  + summary (если есть)
  + последние N сообщений (role + content)
  + новый вопрос юзера
```

### Как работает

1. API загружает `conversation.context` (summary + summary_up_to)
2. Загружает messages после summary_up_to
3. Шлёт Gemini: system_prompt + summary + последние messages + вопрос
4. После ответа: если messages > порога — вызывает Gemini для суммаризации, обновляет `context`

### DB

Колонка `context` (jsonb, nullable) в `conversations`:

```json
{
  "summary": "Обсуждали пятницы NQ 2024, самая волатильная 15 марта (range 380), сравнивали с понедельниками",
  "summary_up_to": 20
}
```

`null` — суммаризации ещё не было, шлём полную историю.

### Почему не RAG / не embeddings

- История — чистый текст, лёгкий
- Gemini 1M контекст — хватит надолго
- Implicit caching Gemini автоматически кэширует повторяющийся system prompt
- RAG нужен когда данных больше чем влезает в контекст. У нас данные считаются tools, в контекст не попадают

## Что сюда НЕ входит

- **Streaming (SSE)** — отдельная фича, связана с chat UI
- **Rate limiting** — добавим когда пойдут реальные юзеры
