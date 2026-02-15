# Query Engine (barb/)

Ядро системы. Принимает JSON-запрос, выполняет по шагам, возвращает результат.

## Как работает

Запрос — плоский JSON. Каждое поле — шаг пайплайна. Порядок выполнения фиксированный, не зависит от порядка полей в JSON.

```
Входные данные (минутный DataFrame)
    ↓
1. session    — фильтр по торговой сессии (RTH, ETH)
2. period     — фильтр по периоду ("2024", "2024-03", "2024-01:2024-06", "2023:", "last_month")
3. from       — ресемплинг таймфрейма ("1m", "5m", "15m", "30m", "1h", "daily", "weekly")
4. map        — вычисляемые колонки {"name": "expression"}
5. where      — фильтр строк по условию (expression)
6. group_by   — группировка (по колонке из map)
7. select     — агрегация ("count()", "mean(col)", ["sum(x)", "max(y)"])
8. sort       — сортировка ("column desc" или "column asc")
9. limit      — ограничение количества строк
    ↓
Результат (summary для модели + table для UI)
```

## Модули

### interpreter.py
Оркестратор. Принимает `execute(query, df, sessions)`, прогоняет по шагам, возвращает результат с summary (для модели) и table (для UI). Валидирует входные данные — неизвестные поля, невалидные таймфреймы, пустые запросы.

### expressions.py
Парсер и вычислитель выражений. Безопасный — никакого eval/exec. Строит AST из строки, вычисляет на DataFrame. Поддерживает:
- Арифметику: `+`, `-`, `*`, `/`
- Сравнения: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Булеву логику: `and`, `or`, `not`
- Membership: `in [1, 2, 3]`
- Функции: `prev()`, `rolling_mean()`, `dayofweek()`, etc.
- Автоконвертация дат: `date() >= '2024-03-15'`

### functions.py
Реестр 40+ функций:
- Скалярные — `abs`, `log`, `round`, `if`
- Лаговые — `prev`, `next` (сдвиг на N баров)
- Оконные — `rolling_mean`, `rolling_sum`, `rolling_max`, `rolling_min`, `rolling_std`, `ema`
- Кумулятивные — `cumsum`, `cummax`, `cummin`
- Паттерны — `streak`, `bars_since`, `rank`
- Агрегатные — `mean`, `sum`, `count`, `max`, `min`, `std`, `median`
- Временные — `dayofweek`, `dayname`, `hour`, `minute`, `month`, `year`, `date`

### data.py
Загрузка Parquet файлов. Один файл = один инструмент. Кэшируется через lru_cache. Возвращает DataFrame с DatetimeIndex и колонками [open, high, low, close, volume].

## Пример

Запрос: "дни когда цена упала на 2.5% и более за 2024"

```json
{
  "session": "RTH",
  "period": "2024",
  "from": "daily",
  "map": {"change_pct": "(close - prev(close)) / prev(close) * 100"},
  "where": "change_pct <= -2.5",
  "sort": "change_pct asc"
}
```

Результат:
- summary: `{type: "table", rows: 13, stats: {change_pct: {min: -5.06, max: -2.51}}}`
- table: 13 строк с датами и данными
