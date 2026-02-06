ну # E2E Test Scenarios

Сценарии для тестирования assistant через полный pipeline.
Каждый сценарий — это переписка пользователя с моделью.

## Что тестируем

| # | Сценарий | Тип | Что проверяет |
|---|----------|-----|---------------|
| 1 | Simple scalar | Скаляр | Базовый flow: reference → confirm → execute → commentary |
| 2 | Correction flow | Коррекция | Пользователь поправляет параметры до выполнения |
| 3 | Table + follow-up | Таблица + follow-up | Запрос таблицы, затем модификация (добавить колонку) |
| 4 | Group-by analysis | Группировка | group_by + select, правильный map |
| 5 | Knowledge question | Знание | Ответ без query, не должна вызывать tools |
| 6 | Multi-step deep dive | Глубокий анализ | Длинная цепочка: скаляр → таблица → фильтр → новый запрос |
| 7 | Unsupported request | Ограничение | Модель честно говорит что не поддерживается |

---

## Scenario 1: Simple scalar

**Цель**: базовый цикл — reference, подтверждение, выполнение, комментарий.

```
User: What is the average daily range for NQ?
  → expect: confirmation sentence, no execute yet
User: yes
  → expect: execute_query, scalar result, short commentary
```

**Проверки**:
- turn 1: get_query_reference вызван, execute_query НЕ вызван
- turn 2: execute_query вызван, data block со скаляром
- Ответ на языке пользователя (English)

---

## Scenario 2: Correction flow

**Цель**: пользователь корректирует параметры перед выполнением.

```
User: Сколько дней цена падала более чем на 2%?
  → expect: confirmation с RTH (default session)
User: используй сессию ETH и период 2024
  → expect: execute_query с session=ETH, period=2024
```

**Проверки**:
- turn 1: confirmation, НЕ execute
- turn 2: execute_query с правильными параметрами (ETH, 2024), data block
- Модель НЕ переспрашивает после коррекции — сразу выполняет

---

## Scenario 3: Table + follow-up

**Цель**: запрос таблицы, затем модификация — добавить колонку.

```
User: покажи топ-5 самых волатильных дней за 2024 год
  → expect: confirmation
User: да
  → expect: execute_query, таблица 5 строк
User: добавь название дня недели
  → expect: execute_query (новый запрос с dayname), 5 строк
```

**Проверки**:
- turn 2: таблица, 5 строк, sort desc, limit 5
- turn 3: execute_query вызван СРАЗУ (без переспрашивания), 5 строк с dayname
- Модель понимает что "добавь" = модифицируй предыдущий запрос

---

## Scenario 4: Group-by analysis

**Цель**: группировка с агрегацией.

```
User: What is the average volume by day of week for 2024?
  → expect: confirmation
User: go
  → expect: execute_query с group_by, таблица 5 строк (пн-пт)
```

**Проверки**:
- execute_query: map содержит dayofweek(), group_by по mapped колонке
- Результат: 5 строк (или 7 если включая weekend)
- Ответ на English

---

## Scenario 5: Knowledge question

**Цель**: ответ без query.

```
User: What is an inside day?
  → expect: текстовый ответ, НИ ОДИН tool не вызван
```

**Проверки**:
- НЕТ вызовов get_query_reference
- НЕТ вызовов execute_query
- Ответ содержит определение (high < prev high, low > prev low)

---

## Scenario 6: Multi-step deep dive

**Цель**: длинная аналитическая цепочка с несколькими запросами.

```
User: сколько inside days было за 2024 год?
  → expect: confirmation
User: давай
  → expect: execute_query, скаляр (count)
User: покажи эти дни
  → expect: execute_query (таблица без select), строки
User: какой был средний range в эти дни?
  → expect: execute_query (новый запрос с select mean), скаляр
```

**Проверки**:
- turn 2: скаляр (count)
- turn 3: execute_query СРАЗУ без confirmation (follow-up к предыдущему)
- turn 4: execute_query СРАЗУ (follow-up), скаляр
- Всего 3+ execute_query вызовов за сценарий

---

## Scenario 7: Unsupported request

**Цель**: модель честно говорит что запрос не поддерживается.

```
User: Compare the daily range of NQ with weekly range in one table
  → expect: объяснение что cross-timeframe не поддерживается, предложение альтернативы
```

**Проверки**:
- Модель НЕ пытается выполнить невозможный запрос
- Предлагает альтернативу (два отдельных запроса)
- Нет ошибок от execute_query

---

## Паттерны поведения которые тестируем

### Confirmation flow
- Сценарии 1, 2, 4: стандартный confirmation
- Сценарий 2: correction вместо confirmation → execute сразу
- Сценарии 3, 6: follow-up после данных → execute сразу, БЕЗ повторного confirmation

### Tool usage
- Сценарий 5: НОЛЬ tool calls
- Сценарий 7: get_query_reference вызван, execute_query НЕТ
- Остальные: reference + execute

### Error recovery
- Покрывается имплицитно — если модель ошибётся в query, engine вернёт ошибку с подсказкой, модель должна retry

### Language
- Сценарии 1, 4, 5, 7: English
- Сценарии 2, 3, 6: Russian
- Ответ должен быть на языке пользователя
