# Barb Script — концепция

## Проблема

LLM генерирует pandas-код для анализа торговых данных. Код содержит баги. Retry помогает частично, но не решает проблему.

## Решение

Декларативный язык запросов. LLM генерирует не код, а описание. Мы интерпретируем.

---

## Фундамент

### Что такое торговые данные?

Временной ряд. Точки с timestamp и значениями:
```
timestamp, open, high, low, close, volume
```

### Какие операции возможны над временным рядом?

**9 примитивов. Не больше.**

| # | Операция | Что делает | Пример |
|---|----------|------------|--------|
| 1 | **MAP** | Преобразовать каждую точку | `range = high - low` |
| 2 | **LAG** | Доступ к прошлым значениям | `prev_close = close[-1]` |
| 3 | **WINDOW** | Скользящее окно | `sma_20 = mean(close, 20)` |
| 4 | **FILTER** | Выбрать подмножество | `where volume > 1000000` |
| 5 | **AGGREGATE** | Свернуть в скаляр | `mean(close) → число` |
| 6 | **GROUP** | Разбить + агрегировать | `group by weekday` |
| 7 | **RESAMPLE** | Изменить гранулярность | `minute → daily` |
| 8 | **JOIN** | Соединить с другим источником | `join events on date` |
| 9 | **SORT/LIMIT** | Упорядочить, ограничить | `order by x desc limit 10` |

### Любой анализ — пайплайн

```
source → resample → map → filter → group → aggregate → sort → output
```

---

## Модель данных

### Источник

```
minute   — исходные 1-минутные бары
```

### Базовые колонки

```
timestamp : datetime
open      : float
high      : float
low       : float
close     : float
volume    : int
```

### Внешние источники (для JOIN)

```
events    — FOMC, NFP, CPI, etc.
holidays  — праздники, early close
```

---

## Примитивы

### 1. MAP — вычислить новую колонку

Формула над существующими колонками.

```yaml
map:
  range: "high - low"
  body: "abs(close - open)"
  gap: "open - prev(close)"
  direction: "sign(close - open)"
```

**Доступные функции:**
- Арифметика: `+`, `-`, `*`, `/`
- Математика: `abs()`, `log()`, `sqrt()`, `sign()`
- Сравнение: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Логика: `and`, `or`, `not`
- Условие: `if(cond, then, else)`

### 2. LAG — доступ к прошлым значениям

```yaml
map:
  prev_close: "prev(close)"      # close[-1]
  prev_high: "prev(high)"        # high[-1]
  change: "close - prev(close)"  # разница
  pct_change: "(close - prev(close)) / prev(close)"
```

**Функции:**
- `prev(col)` — предыдущее значение
- `prev(col, n)` — значение n баров назад

### 3. WINDOW — скользящее окно

```yaml
map:
  sma_20: "mean(close, 20)"
  highest_5: "max(high, 5)"
  lowest_5: "min(low, 5)"
  atr_14: "mean(range, 14)"
  vol_avg: "mean(volume, 20)"
```

**Функции:**
- `mean(col, n)` — скользящее среднее
- `sum(col, n)` — скользящая сумма
- `max(col, n)` — максимум за n баров
- `min(col, n)` — минимум за n баров
- `std(col, n)` — стандартное отклонение

### 4. FILTER — выбрать подмножество

```yaml
filter: "volume > 1000000"
filter: "weekday == 1"
filter: "gap > 0 and close > open"
filter: "high < prev(high) and low > prev(low)"  # inside day
```

### 5. AGGREGATE — свернуть в скаляр

```yaml
aggregate: "mean(volume)"
aggregate: "sum(volume)"
aggregate: "count()"
aggregate: "max(high)"
aggregate: "min(low)"
aggregate: "std(close)"
aggregate: "correlation(a, b)"
aggregate: "percentile(range, 0.95)"
```

### 6. GROUP — разбить + агрегировать

```yaml
group_by: "weekday"
aggregate: "mean(volume)"
```

Результат — таблица с группой и агрегатом.

```yaml
group_by: ["year", "month"]
aggregate: ["mean(volume)", "mean(range)"]
```

### 7. RESAMPLE — изменить гранулярность

```yaml
resample: "D"   # daily
resample: "W"   # weekly
resample: "M"   # monthly
resample: "H"   # hourly
```

При ресемплинге:
- open → first
- high → max
- low → min
- close → last
- volume → sum

### 8. JOIN — соединить с другим источником

```yaml
join:
  source: "events"
  on: "date"
```

После join доступны колонки из events:
```yaml
filter: "event_type == 'FOMC'"
```

### 9. SORT / LIMIT

```yaml
sort: "volume desc"
limit: 10
```

---

## Формат запроса

```yaml
# Пайплайн операций
pipeline:
  - resample: "D"
  - map:
      range: "high - low"
      weekday: "dayofweek(timestamp)"
  - filter: "weekday in [0, 4]"
  - group_by: "weekday"
  - aggregate: "mean(volume)"
```

Или в JSON:

```json
{
  "pipeline": [
    {"resample": "D"},
    {"map": {"range": "high - low", "weekday": "dayofweek(timestamp)"}},
    {"filter": "weekday in [0, 4]"},
    {"group_by": "weekday"},
    {"aggregate": "mean(volume)"}
  ]
}
```

---

## Примеры

### Средний объём понедельников vs пятниц

```yaml
pipeline:
  - resample: "D"
  - map:
      weekday: "dayofweek(timestamp)"
  - filter: "weekday in [0, 4]"
  - group_by: "weekday"
  - aggregate: "mean(volume)"
```

### Gap fill в первый час RTH

```yaml
pipeline:
  - filter: "time >= 09:30 and time < 10:30"
  - resample: "D"
  - map:
      gap: "open - prev(close)"
      gap_filled: "low <= prev(close) or high >= prev(close)"
  - filter: "gap != 0"
  - aggregate: "mean(gap_filled)"  # процент
```

### Самый волатильный день недели

```yaml
pipeline:
  - resample: "D"
  - map:
      range: "high - low"
      weekday: "dayofweek(timestamp)"
  - group_by: "weekday"
  - aggregate: "mean(range)"
  - sort: "mean_range desc"
  - limit: 1
```

### Inside days за год

```yaml
pipeline:
  - resample: "D"
  - filter: "timestamp >= 2024-01-01"
  - map:
      is_inside: "high < prev(high) and low > prev(low)"
  - filter: "is_inside"
  - aggregate: "count()"
```

### Средний range в дни FOMC

```yaml
pipeline:
  - resample: "D"
  - map:
      range: "high - low"
  - join:
      source: "events"
      on: "date"
  - filter: "event_type == 'FOMC'"
  - aggregate: "mean(range)"
```

### Что происходит после NR7

```yaml
pipeline:
  - resample: "D"
  - map:
      range: "high - low"
      is_nr7: "range == min(range, 7)"
      next_range: "next(range)"  # следующий день
  - filter: "is_nr7"
  - aggregate: "mean(next_range)"
```

### Корреляция overnight и RTH range

```yaml
pipeline:
  - resample: "D"
  - map:
      overnight_range: "overnight_high - overnight_low"
      rth_range: "rth_high - rth_low"
  - aggregate: "correlation(overnight_range, rth_range)"
```

---

## Выражения

### Арифметика
```
high - low
close * volume
(high + low) / 2
```

### Сравнения
```
close > open
volume >= 1000000
weekday == 1
```

### Логика
```
close > open and volume > 1000000
not (high < prev(high))
```

### Условия
```
if(close > open, 1, -1)
if(gap > 0, "up", if(gap < 0, "down", "flat"))
```

### Функции времени
```
dayofweek(timestamp)   # 0-6
hour(timestamp)        # 0-23
month(timestamp)       # 1-12
year(timestamp)
date(timestamp)        # только дата
time(timestamp)        # только время
```

---

## Что НЕ поддерживается

1. **Произвольный Python** — только выражения над колонками
2. **Рекурсия** — нет циклов, только пайплайн
3. **Побочные эффекты** — нет записи, только чтение
4. **Неограниченные window** — только фиксированный размер окна

---

## Архитектура

```
┌─────────────────┐
│  "вопрос"       │
└────────┬────────┘
         ↓
┌─────────────────┐
│   Understander  │  ← LLM понимает, переспрашивает
└────────┬────────┘
         ↓
┌─────────────────┐
│   Query Gen     │  ← LLM генерит pipeline JSON
└────────┬────────┘
         ↓
┌─────────────────┐
│   Validator     │  ← проверка синтаксиса
└────────┬────────┘
         ↓
┌─────────────────┐
│   Interpreter   │  ← выполнение (pandas)
└────────┬────────┘
         ↓
┌─────────────────┐
│   Результат     │
└─────────────────┘
```

---

## Преимущества

- **Надёжность** — интерпретатор написан нами, без багов LLM
- **Предсказуемость** — 9 примитивов, конечный набор операций
- **Оптимизация** — можем оптимизировать пайплайн
- **Безопасность** — нет произвольного кода

## Открытые вопросы

1. Как выразить сессии (RTH, overnight)? Как фильтр по времени или отдельный примитив?
2. Как выразить `next()` — доступ к будущим значениям? Нужно ли?
3. Насколько сложные выражения разрешить? Есть ли граница?
4. Как обрабатывать ошибки в пайплайне?
