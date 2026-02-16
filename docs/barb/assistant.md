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

Два tool'а: `BARB_TOOL` (run_query) и `BACKTEST_TOOL` (run_backtest). Dispatch по `tu["name"]` в цикле tool_uses → `_exec_query()` или `_exec_backtest()`. Оба возвращают `(model_response, block)`.

Параметры модели:
- model: `claude-sonnet-4-5-20250929`
- max_tokens: 4096
- temperature: 0 (детерминистичные ответы)

### prompt/ (package)
Строит system prompt из конфига инструмента. Два файла:

**system.py** — `build_system_prompt(instrument)`. Собирает промпт из секций:
- Identity ("You are Barb — a trading data analyst...")
- `<instrument>`, `<holidays>`, `<events>` — контекстные блоки из config (символ, биржа, сессии, данные)
- `<behavior>` — 9 правил поведения (включая #9 для бэктеста)

**context.py** — `build_instrument_context(config)`, `build_holiday_context(config)`, `build_event_context(config)`. Генерируют контекстные блоки из instrument config (сессии, праздники, экономические события).

### context.py (top-level)
Sliding window + summarization для длинных разговоров.

- `SUMMARY_THRESHOLD = 20` — после 20 обменов запускается суммаризация
- `WINDOW_SIZE = 10` — последние 10 обменов сохраняются полностью
- `build_history_with_context()` — подставляет summary + recent messages
- `summarize()` — вызывает Claude (без tools) для сжатия старых сообщений в 3-5 предложений

### tools/
Два инструмента: **run_query** и **run_backtest**

**run_query** (`tools/__init__.py`) — JSON-запрос Barb Script, выполняет через interpreter, возвращает:
- `model_response` — компактный summary для модели
- `table` — полные данные для UI
- `source_rows` — исходные строки (для агрегаций)
- `source_row_count` — количество исходных строк
- `chart` — chart hints (category, value columns) для фронтенда

`chat.py._exec_query()` дополнительно извлекает `metadata` (session, timeframe) из interpreter result и включает в UI block.

**run_backtest** (`tools/backtest.py`) — тестирование торговой стратегии. Принимает strategy (entry expression, direction, stop/take/target/exit_bars/slippage), session, period, title. Возвращает:
- `model_response` — компактная строка с метриками (trades, win rate, PF, P&L, drawdown)
- `backtest` — полные данные для UI (type: "backtest", metrics, trades, equity_curve, strategy)

Обёртка `run_backtest_tool()` конвертирует dict → Strategy → `barb.backtest.run_backtest()` и сериализует `datetime.date` → ISO string. Подробности: `docs/barb/backtest.md`.

### tools/reference.py
Авто-генерация reference для tool description из `SIGNATURES` + `DESCRIPTIONS` dicts. Заменяет статический `expressions.md`. Добавляешь функцию в `barb/functions/` → она автоматически появляется в промпте.

Формат: display groups (compact для утилит, expanded с описаниями для индикаторов).

## Prompt Caching

System prompt кэшируется через `cache_control: {"type": "ephemeral"}`. Повторные запросы к тому же инструменту получают system prompt из кэша. Pricing (Sonnet 4.5): $3/MTok input, $0.30/MTok cached read, $3.75/MTok cache write, $15/MTok output.

## Tool Calls

Каждый вызов логируется в Supabase (таблица `tool_calls`):
- message_id — FK на messages
- tool_name, input (jsonb), output (jsonb)
- error (если был)
- duration_ms
