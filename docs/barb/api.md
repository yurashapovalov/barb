# API (api/)

HTTP-слой. FastAPI с SSE streaming.

## Endpoints

### Health
- `GET /health` — проверка здоровья, без авторизации

### Conversations
- `POST /api/conversations` — создать новый разговор
- `GET /api/conversations` — список разговоров пользователя
- `GET /api/conversations/{id}/messages` — сообщения разговора
- `DELETE /api/conversations/{id}` — удалить разговор

### Chat
- `POST /api/chat/stream` — SSE streaming endpoint

## Авторизация

Supabase JWT. Фронт получает токен через Google OAuth, шлёт в `Authorization: Bearer <token>`. Бэкенд валидирует подпись через SUPABASE_JWT_SECRET (HS256, audience="authenticated").

Нет токена или невалидный → 401. Токен истёк → 401 "Token expired".

## SSE Streaming

`POST /api/chat/stream` возвращает Server-Sent Events:

```
event: title_update
data: {"title": "..."}

event: text_delta
data: {"delta": "Считаю..."}

event: tool_start
data: {"tool_name": "run_query", "input": {...}}

event: tool_end
data: {"tool_name": "run_query", "duration_ms": 1234, "error": null}

event: data_block
data: {"result": [...], "rows": 13, "title": "..."}

event: done
data: {"answer": "...", "usage": {...}, "tool_calls": [...], "data": [...]}

event: persist
data: {"message_id": "...", "persisted": true}
```

## Поток запроса

```
POST /api/chat/stream {conversation_id, message}
    ↓
1. get_current_user() — валидация JWT
2. Загрузка истории из Supabase (messages + tool_calls)
3. _get_assistant(instrument) — из кэша или создаёт новый
4. assistant.chat_stream() — Claude + tool calling
5. SSE events стримятся клиенту
6. После done — сохранение в Supabase (user msg + assistant msg + tool_calls)
7. persist event подтверждает сохранение
```

## Кэширование

Assistant кэшируется per instrument через lru_cache. Один Assistant = один anthropic.Client + загруженный DataFrame. При первом запросе с инструментом — создаётся, дальше переиспользуется.

## Логирование

Production — JSON формат (ts, level, logger, msg). Development — plaintext. Каждый запрос логирует: user id, latency, стоимость.
