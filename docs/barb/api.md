# API (api/)

HTTP-слой. FastAPI с SSE streaming.

## Startup

При старте `_load_instruments()` загружает все инструменты из Supabase view `instrument_full` в кэш `config/market/instruments.py`. Без этого ни один endpoint с инструментами не работает.

## CORS

`CORSMiddleware` с origins из `CORS_ORIGINS` env var (default `*`). Expose `X-Request-Id` header для клиентского логирования.

## Endpoints

### Health
- `GET /health` — проверка здоровья (supabase, anthropic, data), без авторизации

### Instruments
- `GET /api/instruments` — список инструментов (search, category фильтры), без авторизации
- `GET /api/instruments/{symbol}/ohlc` — все daily OHLC бары для инструмента, без авторизации

### User Instruments
- `GET /api/user-instruments` — инструменты пользователя (workspace)
- `POST /api/user-instruments` — добавить инструмент в workspace
- `DELETE /api/user-instruments/{symbol}` — удалить инструмент из workspace

### Conversations
- `POST /api/conversations` — создать новый разговор
- `GET /api/conversations` — список разговоров пользователя (instrument фильтр)
- `GET /api/conversations/{id}/messages` — сообщения разговора
- `DELETE /api/conversations/{id}` — soft delete (status → "removed")

### Chat
- `POST /api/chat/stream` — SSE streaming endpoint. Валидация: `message` min 1, max 10000 символов.

### Admin
- `POST /api/admin/reload-data?token=ADMIN_TOKEN` — очистка кэшей load_data и _get_assistant

## Авторизация

Supabase JWT через JWKS. Фронт получает токен через Google OAuth или magic link (email OTP), шлёт в `Authorization: Bearer <token>`. Бэкенд получает signing key через JWKS endpoint (`/auth/v1/.well-known/jwks.json`), валидирует подпись (ES256, audience="authenticated").

Нет токена или невалидный → 401. Токен истёк → 401 "Token expired".

`GET /health`, `GET /api/instruments`, `GET /api/instruments/{symbol}/ohlc` — без авторизации.

## SSE Streaming

`POST /api/chat/stream` возвращает Server-Sent Events:

```
event: title_update
data: {"title": "..."}

event: text_delta
data: {"delta": "Считаю..."}

event: tool_start
data: {"tool_name": "run_query", "input": {"query": {...}, "title": "..."}}

event: tool_end
data: {"tool_name": "run_query", "duration_ms": 1234, "error": null}

event: data_block (run_query)
data: {"query": {...}, "result": [...], "rows": 13, "columns": ["date", "open", "high", "low", "close", "volume"], "session": "RTH", "timeframe": "daily", "source_rows": [...] | null, "source_row_count": 80 | null, "title": "...", "chart": {"category": "...", "value": "..."}}
// source_rows: separate evidence only for aggregations with table_data.
// When result already IS the evidence (no table_data) — source_rows is null.

event: data_block (run_backtest)
data: {"type": "backtest", "title": "...", "strategy": {...}, "metrics": {"total_trades": 53, "win_rate": 49.1, "profit_factor": 1.32, ...}, "trades": [{"entry_date": "2024-01-15", "exit_date": "2024-01-16", "pnl": 52.5, ...}], "equity_curve": [52.5, 17.8, ...]}
// Type discrimination: query blocks have no "type" field, backtest blocks have type: "backtest".

event: done
data: {"answer": "...", "usage": {...}, "tool_calls": [...], "data": [...]}

event: persist
data: {"message_id": "...", "persisted": true}

event: error
data: {"error": "Service temporarily unavailable"}
```

### Title auto-update

Если title разговора "New conversation", первое сообщение пользователя (обрезанное до 80 символов) становится title. Обновляется в БД и отправляется как `title_update` SSE event до начала ответа модели.

## Поток запроса

```
POST /api/chat/stream {conversation_id, message}
    ↓
1. get_current_user() — валидация JWT через JWKS
2. Загрузка conversation из Supabase, проверка ownership
3. _get_assistant(instrument) — из lru_cache или создаёт новый
4. Загрузка истории (messages + tool_calls для контекста)
5. build_history_with_context() — sliding window + summary
6. Title auto-update (если "New conversation")
7. assistant.chat_stream() — Claude + tool calling (до 5 раундов)
8. SSE events стримятся клиенту
9. После done — _persist_chat() сохраняет в Supabase (user msg + assistant msg + tool_calls + usage)
10. persist event подтверждает сохранение
11. _maybe_summarize() — если порог достигнут, суммаризирует старые сообщения (best effort)
```

## Кэширование

Assistant кэшируется per instrument через `@lru_cache`. Один Assistant = один `anthropic.Anthropic` client + instrument + sessions + два DataFrame (daily + minute) + system prompt. При первом запросе с инструментом — создаётся, дальше переиспользуется.

`POST /api/admin/reload-data` очищает оба кэша — `load_data` и `_get_assistant`. Следующий запрос пересоздаст Assistant с свежими DataFrames из parquet файлов.

## Ошибки

`api/errors.py` регистрирует обработчики для HTTP, validation и unhandled exceptions. Формат: `{"error": "...", "code": "...", "request_id": "..."}`.

## Логирование

Production — JSON формат `{ts, level, logger, msg, request_id}`. Development — plaintext. `RequestIdMiddleware` генерирует request_id и кладёт в ContextVar, `RequestIdFilter` инжектит его в каждый log record. Каждый запрос логирует: user id, conversation id, latency, стоимость.
