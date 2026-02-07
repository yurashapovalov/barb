# Assistant (assistant/)

LLM-слой. Anthropic Claude с tool calling. Переводит естественный язык в JSON-запросы Query Engine.

## Как работает

```
Пользователь: "Какой средний дневной диапазон NQ за 2024?"
    ↓
Claude получает system prompt + историю + сообщение
    ↓
Claude пишет acknowledgment: "Считаю средний диапазон..."
    ↓
Claude вызывает run_query({session: "RTH", from: "daily", ...})
    ↓
Query Engine возвращает summary + table
    ↓
Claude формулирует ответ на основе summary
```

Максимум 5 раундов tool calling за один запрос. Обычно 1-2.

## Модули

### chat.py
Класс `Assistant`. Использует `anthropic.Anthropic` клиент с prompt caching. Стримит ответ через generator, yielding SSE events: `text_delta`, `tool_start`, `tool_end`, `data_block`, `done`.

Параметры модели:
- model: `claude-sonnet-4-5-20250929`
- max_tokens: 4096
- temperature: 0 (детерминистичные ответы)

### prompt.py
Строит system prompt из конфига инструмента. Включает:
- Роль и контекст (символ, биржа, диапазон данных, сессии)
- Инструкции по workflow
- Секцию `<acknowledgment>` — модель пишет 15-20 слов перед tool call
- Секцию `<data_titles>` — модель даёт название каждому результату
- Примеры использования

### tools/
Один инструмент: **run_query**

Принимает JSON-запрос Barb Script, выполняет через interpreter, возвращает:
- `model_response` — компактный summary для модели
- `table` — полные данные для UI
- `source_rows` — исходные строки (для агрегаций)

Tool description включает полную спецификацию Barb Script + expressions.md.

## Prompt Caching

System prompt кэшируется через `cache_control: {"type": "ephemeral"}`. После первого запроса ~90% токенов читаются из кэша (0.30$/MTok вместо 3$/MTok).

## Tool Calls

Каждый вызов логируется в Supabase (таблица `tool_calls`):
- tool_name, input, output
- error (если был)
- duration_ms
