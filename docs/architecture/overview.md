# Архитектура Barb

Торговый аналитический ассистент. Пользователь задаёт вопрос на естественном языке — получает ответ с данными.

## Слои

```
Пользователь
    ↓
Frontend (React + Supabase)     — UI, авторизация, история чатов
    ↓ JWT
API (FastAPI + Supabase)        — валидация токена, CRUD, SSE streaming
    ↓
Assistant (Claude + run_query)  — LLM думает, вызывает инструмент
    ↓
Query Engine (barb/)            — детерминированное выполнение запросов
    ↓
Data (Parquet)                  — минутные OHLCV данные
```

## Принципы

- **LLM — мозг, Query Engine — руки.** LLM решает что считать, Query Engine считает. Никакого произвольного кода — только JSON-запросы через фиксированный пайплайн.
- **Stateless API.** Сервер не хранит состояние между запросами. История загружается из Supabase.
- **Конфиг, не код.** Инструменты, сессии, праздники — всё в config/. Промпт строится из конфига, не захардкожен.
- **SSE streaming.** Ответы модели стримятся через Server-Sent Events — пользователь видит текст по мере генерации.

## Модули

- [Query Engine (barb/)](./query-engine.md) — пайплайн обработки запросов
- [Assistant (assistant/)](./assistant.md) — LLM + tool calling
- [API (api/)](./api.md) — HTTP слой
- [Config (config/)](./config.md) — конфигурация инструментов, рынка
- [Frontend (front/)](./frontend.md) — React приложение
- [Инфраструктура](./infrastructure.md) — деплой, CI, Docker
- [Result Format](./result-format.md) — формат данных для модели и UI
