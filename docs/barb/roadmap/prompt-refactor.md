# Рефакторинг промпта

## Проблема

System prompt ~140 строк. Всё свалено в кучу: identity, контекст инструмента, правила поведения, рецепты, примеры, правила форматирования, transparency. Claude частично игнорирует инструкции потому что всё конкурирует за внимание на одном уровне приоритета.

Function reference (106 функций) живёт в tool description — правильное место. Но правила поведения, примеры запросов и микро-правила (acknowledgment, data_titles, transparency) сидят в system prompt где разбавляют основное сообщение.

## Что говорит Anthropic

Из [официальной документации](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices):

**1. "Be explicit with your instructions"**
Claude 4.x точно следует инструкциям. Не нужно объяснять по пять раз. Одно чёткое предложение лучше пяти расплывчатых.

**2. "Tune anti-laziness prompting"**
Если в промпте были агрессивные инструкции типа "ВСЕГДА делай X" — убрать. Claude Opus 4.6 / Sonnet 4.5 перестараются и будут overtrigger-ить.

**3. "Use XML tags to structure prompts"**
Теги `<instructions>`, `<examples>` помогают Claude различать части промпта. Без них Claude может перепутать инструкции с примерами.

**4. "Put longform data at the top"**
Длинные документы вверху, запрос внизу. Улучшает качество ответов на 30%.

**5. Tool description = часть промпта**
Claude читает описание тула когда решает его вызвать. Знания о том КАК использовать тул — в tool description, не в system prompt.

**6. "Add context to improve performance"**
Объясни ПОЧЕМУ правило существует, не только ЧТО. Claude обобщает из объяснений.

## Текущая структура

```
System prompt (~140 строк):
  Identity                    3 строки   ← ок
  <instrument>               ~15 строк   ← ок, динамический контекст
  <holidays>                 ~5 строк    ← ок
  <events>                   ~10 строк   ← ок
  <recipes>                   8 строк    ← должно быть в tool description
  <instructions>             12 правил   ← смесь поведения и логики запросов
  <transparency>             10 строк    ← микро-менеджмент
  <acknowledgment>            5 строк    ← микро-менеджмент
  <data_titles>               4 строки   ← микро-менеджмент
  <examples>                 40 строк    ← должно быть в tool description

Tool description (run_query):
  Синтаксис запросов         ~20 строк   ← ок
  Function reference        ~100 строк   ← ок, авто-генерация
```

### Что не так

**1. Instructions мешают разные уровни.**
"Отвечай на языке пользователя" (всегда, каждый ход) стоит рядом с "для процентов делай два запроса" (конкретный кейс при вызове тула). Claude воспринимает их с одинаковым весом.

**2. Примеры не на месте.**
Примеры показывают как конструировать JSON-запрос. Это знание о тулe, а не о поведении. Они должны быть в tool description, рядом с синтаксисом.

**3. Три секции для мелочей.**
`<transparency>`, `<acknowledgment>`, `<data_titles>` — три отдельных XML-блока для минорных правил поведения. Можно сжать в 3 строки.

**4. Recipes — это паттерны запросов.**
MACD cross, breakout, NFP filter — это примеры использования тула. Они должны быть в tool description рядом с function reference.

**5. Нет объяснения ПОЧЕМУ.**
"Для процентов делай два запроса" — а почему? Потому что движок не умеет считать проценты, нужно два count(). Claude следует правилам лучше когда понимает причину.

## Предлагаемая структура

### System prompt (~30 строк)

Только: кто ты, как себя вести, динамический контекст рынка.

```
You are Barb — a trading data analyst for {instrument} ({name}).
You help traders explore historical market data through natural conversation.
Users don't need to know technical indicators — you translate their questions into data.

<instrument>
  ... (без изменений — символ, биржа, сессии, тик, период данных)
</instrument>

<holidays>
  ... (без изменений — если есть)
</holidays>

<events>
  ... (без изменений — если есть)
</events>

<behavior>
1. Data questions → call run_query, then comment on results (1-2 sentences).
2. Knowledge questions ("what is RSI?") → answer directly, no tools. 2-4 sentences, offer to explore.
3. Answer in the same language the user writes in.
4. Only cite numbers from tool results. Never invent values.
5. Don't repeat raw numbers — the data table is shown to the user automatically.
6. Before calling run_query, write a brief confirmation (10-20 words) so user sees you understood.
7. Every run_query call must include "title" — a short label for the data card (3-6 words, same language as user).
8. After showing results, briefly mention what you measured and any alternative approaches.
</behavior>
```

**Что изменилось:**
- `<instructions>` сократились с 12 правил до 8 — логика запросов ушла в tool description
- `<transparency>`, `<acknowledgment>`, `<data_titles>` схлопнулись в правила 6, 7, 8
- `<recipes>` переехали в tool description
- `<examples>` переехали в tool description
- Было ~140 строк → стало ~30 строк + динамические блоки контекста

### Tool description (run_query)

Вся информация о запросах: синтаксис, правила, паттерны, примеры, function reference.

```
Execute a Barb Script query against market data.

<syntax>
Query — плоский JSON-объект, все поля опциональные:
- session: сессия (RTH, ETH). Без неё — settlement данные.
- from: "1m", "5m", "15m", "30m", "1h", "daily", "weekly" (по умолчанию: "1m")
- period: "2024", "2024-03", "2024-01:2024-06", "last_year"
- map: {"col": "expression"} — вычислить колонки
- where: "expression" — фильтр строк
- group_by: "column" или ["col1", "col2"] — только имя колонки, не выражение
- select: только агрегатные функции: count(), sum(), mean(), min(), max(),
          std(), median(), percentile(), correlation(), last()
- sort: "column desc" или "column asc"
- limit: число

Порядок выполнения: session → period → from → map → where → group_by → select → sort → limit
</syntax>

<rules>
- group_by принимает ИМЯ КОЛОНКИ. Создай колонку в map, потом группируй.
- Без period → ВСЕ доступные данные. Не придумывай период по умолчанию.
- Сохраняй период из контекста разговора (если пользователь сказал "2024" — используй в продолжении).
- Для процентов: два запроса (общий count + отфильтрованный count).
  Движок не умеет проценты — считай вручную из двух чисел.
- Без session → settlement данные. С session → данные конкретной сессии.
- Используй dayname()/monthname() для читаемого вывода, не dayofweek()/month().
- Используй встроенные функции (rsi, atr, macd, crossover) — не считай вручную.
- Если пользователь спрашивает о празднике → скажи что рынок был закрыт и почему.
</rules>

<patterns>
Частые мультифункциональные паттерны:
  MACD cross      → crossover(macd(close,12,26), macd_signal(close,12,26,9))
  breakout up     → close > rolling_max(high, 20)
  breakdown       → close < rolling_min(low, 20)
  NFP days        → dayofweek() == 4 and day() <= 7
  OPEX            → dayofweek() == 4 and day() >= 15 and day() <= 21
  opening range   → первые 30-60 минут RTH сессии
  closing range   → последние 60 минут RTH сессии
</patterns>

<examples>
Пример 1 — простой фильтр:
"Покажи дни когда рынок упал на 2.5%+ в 2024"
→ {"from":"daily","period":"2024",
   "map":{"chg":"change_pct(close,1)"}, "where":"chg <= -2.5"}
  title: "Падения >2.5%"

Пример 2 — индикатор без периода (все данные):
"Когда рынок был в перепроданности?"
→ {"from":"daily",
   "map":{"rsi":"rsi(close,14)"}, "where":"rsi < 30"}
  title: "Перепроданность"

Пример 3 — group_by (колонка в map, потом группировка):
"Средний рейндж по дням недели за 2024"
→ {"from":"daily","period":"2024",
   "map":{"r":"range()","dow":"dayname()"}, "group_by":"dow", "select":"mean(r)"}
  title: "Рейндж по дням"

Пример 4 — фильтр по событию:
"Средний рейндж в дни NFP?"
→ {"from":"daily","period":"2024",
   "map":{"r":"range()","dow":"dayofweek()","d":"day()"},
   "where":"dow == 4 and d <= 7", "select":"mean(r)"}
  title: "Рейндж NFP"

Пример 5 — follow-up (сохраняй период):
"Средний ATR за 2024?"  →  {"from":"daily","period":"2024",...}
"А за 2023?"            →  {"from":"daily","period":"2023",...}
</examples>

{function_reference}
```

## Почему это лучше

### 1. Разделение ответственности

| | System prompt | Tool description |
|---|---|---|
| **Назначение** | Кто ты, как себя вести | Что умеешь, как этим пользоваться |
| **Меняется** | Для каждого инструмента | Никогда (статично) |
| **Claude читает** | Всегда, каждый ход | Когда решает вызвать тул |
| **Размер** | Маленький (~30 строк + контекст) | Может быть большим (справочник) |

### 2. Распределение внимания

**Сейчас:** Claude видит 140 строк system prompt + tool description каждый ход. Большая часть — синтаксис запросов и примеры, которые нужны только при вызове run_query.

**После:** Claude видит ~30 строк поведения + контекст каждый ход. Детали запросов загружаются в внимание только когда Claude собирается вызвать run_query. Меньше шума = лучше следует инструкциям.

### 3. Масштабируется на несколько тулов

Когда добавим `backtest`, `risk_analysis`, `scan` — у каждого будет своё описание со своими примерами и правилами. System prompt останется на ~30 строках. Без рефакторинга system prompt вырастет до 300+ строк.

### 4. Prompt caching не ломается

System prompt кешируется (первый блок, статичен между ходами). Tool definitions тоже кешируются (не меняются между ходами). Перенос контента между ними не влияет на кеширование — оба в кешированном префиксе.

## Влияние на токены

| | Сейчас | После |
|---|---|---|
| System prompt | ~1,200 токенов | ~400 токенов + контекст |
| Tool description | ~1,500 токенов | ~2,300 токенов |
| **Итого** | ~2,700 токенов | ~2,700 токенов |

Общее количество токенов примерно одинаковое. Разница в том ГДЕ они находятся, что влияет на распределение внимания Claude.

## Связь с display columns

Рефакторинг промпта — возможность научить модель правильно работать с отображением результатов. Сейчас модель не знает о формате вывода (см. `docs/barb/roadmap/display-columns.md`).

### Что модель должна знать о выводе

В секцию `<rules>` tool description нужно добавить:

1. **Автоколонки** — `date` (и `time` для intraday) генерируются автоматически. Не надо маппить `date()` для отображения.
2. **OHLCV** — `open`, `high`, `low`, `close`, `volume` всегда включаются в результат. Не надо маппить их.
3. **Порядок** — колонки выводятся: date, time, group_keys, OHLCV, volume, map-колонки.
4. **Имена map-колонок** — давать на языке пользователя, короткие и понятные.
5. **Контекстная полезность** — если вопрос общий ("покажи торговые дни"), добавь через map что-то полезное (change%, range) — не голые OHLCV.

### Будущее: поле `display`

Если промптовых правил недостаточно (модель всё равно дублирует колонки или показывает лишнее), следующий шаг — поле `display` в запросе, которое даёт модели явный контроль над отображением. Это отдельная задача, но промпт-рефакторинг закладывает фундамент.

## План реализации

### Файлы

| Файл | Что делаем |
|------|-----------|
| `assistant/prompt/system.py` | Переписать `build_system_prompt()` — убрать recipes, examples, transparency, acknowledgment, data_titles. Оставить identity + контекст + `<behavior>` |
| `assistant/tools/__init__.py` | Расширить tool description — добавить `<rules>`, `<patterns>`, `<examples>`, правила про автоколонки |
| `assistant/tools/reference.py` | Без изменений (function reference остаётся) |
| `assistant/prompt/context.py` | Без изменений (instrument/holidays/events остаются) |
| `docs/barb/prompt-architecture.md` | Обновить документацию |
| `tests/test_prompt.py` | Обновить тесты |

### Шаг 1: System prompt (`system.py`)

**Убираем** из system prompt (переезжают в tool description):
- `<recipes>` (строки 43-53) → `<patterns>` в tool description
- `<examples>` (строки 99-138) → `<examples>` в tool description
- Из `<instructions>`: правила 3, 4, 5, 9, 10, 12 (логика запросов) → `<rules>` в tool description

**Убираем** из system prompt (сжимаем в `<behavior>`):
- `<transparency>` (строки 70-82) → правило 8 в `<behavior>`
- `<acknowledgment>` (строки 84-90) → правило 6 в `<behavior>`
- `<data_titles>` (строки 92-97) → правило 7 в `<behavior>`

**Оставляем** в system prompt:
- Identity (строки 37-39) — без изменений
- `<instrument>`, `<holidays>`, `<events>` — без изменений (динамический контекст)
- `<instructions>` → переименовать в `<behavior>`, оставить правила 1, 2, 6, 7, 8 (поведение)

**Новый system prompt** (~30 строк + контекст):

```python
f"""\
You are Barb — a trading data analyst for {instrument} ({config["name"]}).
You help traders explore historical market data through natural conversation.
Users don't need to know technical indicators — you translate their questions into data.

{context_section}

<behavior>
1. Data questions → call run_query, then comment on results (1-2 sentences).
2. Knowledge questions ("what is RSI?") → answer directly, no tools. 2-4 sentences, offer to explore.
3. Answer in the same language the user writes in.
4. Only cite numbers from tool results. Never invent values.
5. Don't repeat raw numbers — the data table is shown to the user automatically.
6. Before calling run_query, write a brief confirmation (10-20 words) so user sees you understood.
7. Every run_query call must include "title" — a short label for the data card (3-6 words, same language as user).
8. After showing results, briefly mention what you measured and any alternative approaches.
</behavior>"""
```

### Шаг 2: Tool description (`tools/__init__.py`)

Расширить описание `BARB_TOOL["description"]`. Текущий контент (синтаксис + IMPORTANT) остаётся, добавляем:

```
<rules>
- group_by requires COLUMN NAME. Create in map first, then group.
- Without period → ALL available data. Don't invent defaults. Keep period context from conversation.
- Percentage questions → TWO queries (total count + filtered count). Engine can't calculate percentages.
- Without session → settlement data. With session → session-specific.
- Use dayname()/monthname() for readable output, not dayofweek()/month().
- Use built-in functions (rsi, atr, macd, crossover) — don't calculate manually.
- If user asks about a holiday → tell them market was closed and why.

Output format:
- Results always include: date column (auto-generated), OHLCV, volume, then map columns.
- Do NOT map date() for display — the date column is created automatically.
- Do NOT map open/high/low/close/volume — they are always included.
- Name map columns in the user's language, short and clear.
- For general questions ("show trading days"), add useful map columns (change_pct, range) — not just bare OHLCV.
</rules>

<patterns>
Common multi-function patterns:
  MACD cross      → crossover(macd(close,12,26), macd_signal(close,12,26,9))
  breakout up     → close > rolling_max(high, 20)
  breakdown       → close < rolling_min(low, 20)
  NFP days        → dayofweek() == 4 and day() <= 7
  OPEX            → dayofweek() == 4 and day() >= 15 and day() <= 21
  opening range   → first 30-60 min of RTH session
  closing range   → last 60 min of RTH session
</patterns>

<examples>
... (5 примеров, переносятся из system.py без изменений)
</examples>

{_EXPRESSIONS_MD}
```

### Шаг 3: Обновить документацию и тесты

- `docs/barb/prompt-architecture.md` — обновить описание структуры
- `tests/test_prompt.py` — обновить assertions (секции изменились)

### Проверка

1. `pytest tests/test_prompt.py` — тесты промпта
2. `pytest tests/` — все тесты
3. Деплой → задать тестовые вопросы:
   - "сколько торговых дней в январе 2026" → нет дублирования `date`/`дата`, map-колонки на русском
   - "покажи RSI ниже 30" → правильный запрос, acknowledgment перед вызовом
   - "средний gap по дням недели за 2024" → group_by с колонкой из map
   - "что такое ATR?" → ответ без tool call
