# Рефакторинг промпта

## Проблема

Модель галлюцинирует данные которые не видит. Пример из продакшена (Feb 2026):

```
Tool result (что видит модель):
  Result: 44 rows
  first: date=2026-01-29, time=09:45
  last: date=2026-02-17, time=10:00

Что модель написала пользователю:
  "Occurred: 5 times — Jan 29, Feb 3, Feb 10, Feb 13, Feb 17"
  "Average move to session high: +127 points"
  "Win rate: 100%"

Реальность:
  - В данных 6 уникальных дат, не 5
  - Feb 10, Feb 13 отсутствуют в данных (Feb 4, Feb 5 есть)
  - "+127 points" и "100% win rate" — полностью выдуманы
```

Модель получает только summary (кол-во рядов, min/max, first/last). Полная таблица уходит напрямую в UI. Модель не видит отдельные строки, но притворяется что видит.

Другой пример: модель захардкодила даты в следующий query (`date() in ['2026-02-10', ...]`) — даты которых нет в данных. Галлюцинация стала входом для следующего tool call.

## Архитектура данных (как это работает)

```
User question
    ↓
Model generates run_query(query={...})
    ↓
Engine executes → returns {summary, table, source_rows, chart}
    ↓
Model gets: summary only (compact text)
UI gets: full table + chart (user sees this directly)
```

### Что модель видит в tool result

**Table result (N rows):**
```
Result: 44 rows
  col_name: min=X, max=Y, mean=Z
  first: date=2026-01-29, time=09:45
  last: date=2026-02-17, time=10:00
```
Модель НЕ видит 44 строк. Только агрегаты + first/last.

**Scalar result:**
```
Result: 21 (from 21 rows)
```
Полный результат — одно число.

**Grouped result:**
```
Result: 5 groups by dow
  min: dow=Friday, mean_r=180.5
  max: dow=Monday, mean_r=245.3
```
Модель видит количество групп + min/max строку. Все группы показаны в UI.

**Backtest result:**
```
Backtest: 53 trades | Win Rate 49.1% | PF 1.32 | ...
Avg win: +171.2 | Avg loss: -124.6 | ...
By year: 2008 +140.9 (16) | 2010 +4.4 (3) | ...
Exits: stop 26 (...) | take_profit 24 (...)
Top 3 trades: +1606.6 pts (147.8% of total PnL)
```
Полный breakdown — backtest summary содержит всё для анализа.

### Корень проблемы

1. **Модель не знает что не видит таблицу.** Нигде в промпте не сказано: "ты получаешь summary, пользователь видит полную таблицу".
2. **Роль "analyst" провоцирует.** Аналитик делает выводы. Модель должна быть интерфейсом.
3. **Запретительные правила не работают.** "Never invent values" — модель не считает что "определить уникальные даты из 44 рядов" это "invent".
4. **Правильное поведение не показано примером.** Нет примера "получил N rows → нужны детали → group_by".

## Текущий промпт — полная анатомия

### 1. System prompt (`assistant/prompt/system.py`)

```python
You are Barb — a trading data analyst for {instrument} ({config["name"]}).
You help traders explore historical market data through natural conversation.
Users don't need to know technical indicators — you translate their questions into data.

<instrument>...</instrument>    # ~15 строк, динамический
<holidays>...</holidays>        # ~5 строк, если есть
<events>...</events>            # ~10 строк, если есть

<behavior>
1. Data questions → call run_query, comment on results (1-2 sentences).
   Knowledge questions → answer directly, 2-4 sentences.
2. Percentage questions → TWO queries (total count + filtered count), calculate %.
3. Without session → settlement data. With session → session-specific.
4. No period specified → use ALL data. Keep period context from conversation.
5. Answer in user's language. Only cite numbers from tool result — never invent values.
6. Don't repeat raw data — it's shown to user automatically.
   Use dayname()/monthname() for readability.
7. Before calling run_query, write a brief confirmation (10-20 words).
   Every call MUST include "title" (3-6 words, user's language).
8. After results, briefly explain what you measured.
   If multiple indicators fit, mention the alternative.
   If you chose a threshold, state it.
9. Strategy testing → call run_backtest. Always include stop_loss.
   After results — analyze strategy QUALITY:
   a) Yearly stability   b) Exit analysis   c) Concentration
   d) Trade count < 30 = warn   e) Suggest variation   f) PF > 2 = skepticism
10. Know your limits. If request needs features Barb doesn't have — say so.
    Don't attempt workarounds that produce misleading results.
</behavior>
```

**Проблемы:**
- Роль "data analyst" → модель думает что может анализировать данные в голове
- `<behavior>` — 10 правил разного характера (протокол, целостность, бэктест, честность)
- Правило 5 слабое: "never invent values" не объясняет ЧТО модель не видит
- Нет объяснения архитектуры: summary vs full table
- Правило 9 (бэктест анализ) далеко от backtest tool

### 2. Tool description — run_query (`assistant/tools/__init__.py`)

~90 строк:
- Описание полей query: session, from, period, map, where, group_by, select, sort, limit
- Output format: columns array
- `<patterns>` — рецепты (MACD cross, breakout, NFP, OPEX)
- `<examples>` — 5 примеров вызовов
- Expression Reference (auto-generated) — все 106 функций

**Проблемы:**
- Примеры показывают **как вызвать** tool, но не **как интерпретировать** результат
- Нет объяснения что модель видит в ответе (summary vs table)
- Нет примера "получил N rows → нужны детали → ещё один query"

### 3. Tool description — run_backtest (`assistant/tools/backtest.py`)

~60 строк:
- Описание полей strategy
- `<patterns>` — entry patterns
- `<examples>` — 3 примера вызовов

**Проблемы:**
- Анализ бэктеста (rule 9) живёт в system prompt, далеко от tool
- Нет примера интерпретации результата

### 4. Размер и кеширование

| Компонент | Токены (≈) | Кешируется? |
|---|---|---|
| System prompt | ~400 | Да (prompt caching) |
| run_query description | ~2,500 | Да |
| run_backtest description | ~800 | Да |
| Expression reference | ~1,200 | Да |
| **Итого кешированного** | **~4,900** | |

Всё в кешированном префиксе. Перемещение контента между system prompt и tool descriptions не влияет на стоимость.

## Принципы рефакторинга

Из Anthropic docs (`docs/antropic/prompt-engineering/`):

### Role prompting (`role.md`)
Роль определяет поведение сильнее чем правила. "Data analyst" → модель анализирует в голове. "Data interface" → модель передаёт данные.

### XML tags (`use-xml-tags.md`)
Разделить concerns по тегам. Каждый блок — одна тема. Prevent mixing up instructions with examples or context.

### Examples (`use-examples.md`)
3-5 примеров правильного поведения > 10 запретительных правил. "Examples reduce misinterpretation of instructions."

### Chain prompts (`chain-complex-prompts.md`)
Каждый subtask gets full attention. Не пытаться всё за один вызов. Применимо: каждый tool call = одна задача.

## Предложение

### System prompt — роль + архитектура + примеры поведения

```python
f"""\
You are Barb — a data interface for {instrument} ({config["name"]}).
You translate user questions into tool calls and present results.
All facts must come from tool results — you never compute, estimate, or list data yourself.

<data-flow>
When you call run_query or run_backtest:
- You receive a SUMMARY: row count, column stats (min/max/mean), first and last row.
- The user sees the FULL TABLE directly in the UI.
- You do NOT see individual rows. Never list dates, prices, or values that aren't in the summary.
- If you need specific values or breakdowns — make another query (group_by, select, where).
</data-flow>

{context_section}

<response-rules>
1. Data questions → call tool, then comment on results (1-2 sentences). Knowledge questions → answer directly.
2. Answer in user's language.
3. Before calling a tool, write a brief confirmation (10-20 words). Every call needs "title" (3-6 words, user's language).
4. Don't repeat data — it's shown to the user. Comment on what the data means.
5. After results, briefly explain what you measured and mention alternatives if relevant.
6. Know your limits. If Barb can't do it — say so. Don't attempt workarounds that mislead.
</response-rules>

<examples>
Good — scalar result, cite directly:
  Summary: "Result: 21 (from 21 rows)"
  Response: "В марте 2025 был 21 торговый день."

Good — table result, summarize what you know:
  Summary: "Result: 12 rows\\n  first: date=2024-01-18\\n  last: date=2024-11-15"
  Response: "RSI опускался ниже 30 в 12 дней за 2024 год."

Good — need details from table, make another query:
  Summary: "Result: 44 rows\\n  first: date=2026-01-29\\n  last: date=2026-02-17"
  → Instead of listing dates, call run_query with group_by to get the breakdown.

Bad — hallucinating data not in summary:
  Summary: "Result: 44 rows\\n  first: date=2026-01-29"
  Response: "This occurred on Jan 29, Feb 3, Feb 10..." ← you don't see these dates

Good — backtest result, analyze quality:
  Summary: "Backtest: 53 trades | Win Rate 49.1% | PF 1.32 | ..."
  Response: analyze yearly stability, exit breakdown, concentration risk (all numbers are in the summary).
</examples>"""
```

### run_query tool description — добавить data protocol

К текущему описанию добавить секцию:

```
<data-protocol>
Your tool result is a SUMMARY — not the full data:
- Table: row count + column stats + first/last row. You don't see individual rows.
- Scalar: the number directly.
- Grouped: group count + min/max group. All groups shown to user.

The user sees the complete table/chart in the UI.
If you need dates, values, or breakdowns not in the summary — run another query.
Never hardcode values you haven't received (e.g. date() in ['...'] with guessed dates).
</data-protocol>
```

### run_query tool description — перенести правила из behavior

```
<query-rules>
- Percentage questions → TWO queries (total count + filtered count). Engine can't compute percentages.
- Without period → ALL data. Keep period context from conversation.
- Without session → settlement data. With session → session-specific.
- Use dayname()/monthname() for readable output.
</query-rules>
```

### run_backtest tool description — перенести анализ из behavior 9

```
<analysis-rules>
After results, analyze strategy QUALITY — don't just repeat numbers:
- Yearly stability: consistent or depends on one period?
- Exit analysis: which exit type drives profits? Stops destroying gains?
- Concentration: top 3 trades dominate PnL → flag fragility.
- Trade count below 30 → warn about insufficient data.
- Suggest one specific variation (tighter stop, trend filter, session filter).
- PF > 2.0 or win rate > 70% → express skepticism, suggest stress testing.
- 0 trades → explain why, suggest relaxing conditions.
</analysis-rules>
```

## Что переносить куда

| Текущее место | Правило | Новое место |
|---|---|---|
| behavior 1 | Data → tool, knowledge → answer | system prompt (response-rules 1) |
| behavior 2 | Percentages → TWO queries | run_query description (query-rules) |
| behavior 3 | Session semantics | run_query description (query-rules) |
| behavior 4 | No period → all data | run_query description (query-rules) |
| behavior 5 | Never invent values | system prompt (data-flow) + examples |
| behavior 6 | Don't repeat raw data | system prompt (response-rules 4) |
| behavior 7 | Brief confirmation + title | system prompt (response-rules 3) |
| behavior 8 | Explain methodology | system prompt (response-rules 5) |
| behavior 9 | Backtest analysis quality | run_backtest description (analysis-rules) |
| behavior 10 | Know your limits | system prompt (response-rules 6) |

## Ключевые изменения

### 1. Роль: "data analyst" → "data interface"
Модель не анализирует данные в голове. Она переводит вопросы в queries и передаёт результаты.

### 2. `<data-flow>` — новая секция
Объясняет архитектуру: что модель видит (summary), что пользователь видит (table). Это корень проблемы галлюцинаций.

### 3. Примеры правильного/неправильного поведения
Вместо "never invent values" — показать конкретно: вот summary, вот правильный ответ, вот галлюцинация. 3-5 примеров (Anthropic docs: "examples reduce misinterpretation").

### 4. Правила рядом с инструментом
Backtest анализ — в backtest tool. Query правила — в query tool. System prompt — только поведение.

### 5. `<behavior>` 10 правил → `<response-rules>` 6 правил
4 правила переехали в tool descriptions. Оставшиеся 6 — про поведение, не про инструменты.

## Верификация

1. `pytest tests/test_prompt.py` — обновить assertions
2. e2e: прогнать все 19 сценариев, сравнить с baseline (results/e2e/)
3. Добавить проблемный сценарий в e2e_scenarios.py (session high/low timing)
4. Проверить: модель НЕ перечисляет данные которых нет в summary
5. Проверить: модель делает доп. query когда нужны детали

## Риски

- Может сломать хорошее поведение — нужно A/B через e2e
- "Data interface" может быть слишком passive — модель перестанет предлагать follow-up вопросы
- Общий размер токенов не меняется, но распределение внимания — да
- Примеры поведения увеличивают system prompt на ~15 строк

## Файлы

```
assistant/prompt/system.py       — переписать: роль + data-flow + examples + response-rules
assistant/tools/__init__.py      — добавить: data-protocol + query-rules
assistant/tools/backtest.py      — добавить: analysis-rules
scripts/e2e_scenarios.py         — добавить проблемный сценарий
docs/barb/prompt-architecture.md — обновить
tests/test_prompt.py             — обновить
```
