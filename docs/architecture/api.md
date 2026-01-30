# API (api/)

HTTP-слой. FastAPI, один endpoint для чата.

## Endpoints

- `GET /health` — проверка здоровья, без авторизации
- `POST /api/chat` — основной endpoint, требует JWT

## Авторизация

Supabase JWT. Фронт получает токен через Google OAuth, шлёт в `Authorization: Bearer <token>`. Бэкенд валидирует подпись через SUPABASE_JWT_SECRET (HS256, audience="authenticated").

Нет токена или невалидный → 401. Токен истёк → 401 "Token expired".

## Поток запроса

```
POST /api/chat
{
  "message": "...",
  "history": [...],
  "instrument": "NQ"
}
    ↓
1. get_current_user() — валидация JWT
2. _get_assistant(instrument) — из кэша или создаёт новый
3. assistant.chat(message, history) — Gemini + tool calling
4. Возвращает ChatResponse
```

## Модели ответа

```
ChatResponse:
  answer      — текст ответа модели
  data[]      — массив DataBlock (результаты запросов для UI)
  usage       — токены + стоимость (input, output, thinking, cached)
  tool_calls[] — лог вызовов тулов (имя, input, output, error, duration_ms)
```

## Кэширование

Assistant кэшируется per instrument через lru_cache. Один Assistant = один genai.Client + загруженный DataFrame. При первом запросе с инструментом — создаётся, дальше переиспользуется.

## Логирование

Production — JSON формат (ts, level, logger, msg). Development — plaintext. Каждый запрос логирует: user id, latency, стоимость.
