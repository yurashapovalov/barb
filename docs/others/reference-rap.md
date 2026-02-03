# Reference RAP Architecture

Retrieval-Augmented Prompting для Barb Script reference.

## Проблема

`get_query_reference` возвращает всё: формат, функции, все примеры. Сейчас ~500 токенов, 7 примеров — терпимо. Но с ростом фич (индикаторы, бэктесты, мульти-таймфрейм) примеров станет 30+, reference вырастет до 2000+ токенов. Модель теряет фокус в большом тексте.

## Решение: секции + паттерны

Разделить reference на:
1. **Format** — всегда отдаётся (поля, execution order, операторы, функции)
2. **Patterns** — примеры, сгруппированные по типу запроса

```
get_query_reference(pattern?)
  │
  ├── format.md (всегда, ~200 токенов)
  │   - Query fields: session, from, period, map, where, group_by, select, sort, limit
  │   - Execution order
  │   - Expression syntax
  │   - Function list (без примеров использования)
  │
  └── patterns/ (по запросу, ~100 токенов каждый)
      ├── simple_stat.md     — scalar: average range, count
      ├── filter_count.md    — where + count: inside days, bullish days
      ├── group_analysis.md  — group_by: volume by weekday, range by month
      ├── pattern_detect.md  — prev, rolling: gaps, NR7
      └── ranking.md         — sort + limit: top N days
```

## Фазы развёртывания

### Фаза 1: Структура (сейчас)

Разбить `_QUERY_REFERENCE` из одного текстового блока на файлы. Загружать все. Никакой фильтрации. Поведение не меняется, но контент организован и готов к фильтрации.

```python
def run(args: dict) -> str:
    # Фаза 1: всегда всё
    return _load_format() + _load_all_patterns()
```

### Фаза 2: Фильтрация (когда примеров >15)

Добавить параметр `pattern` в tool declaration. Модель выбирает паттерн, получает только релевантные примеры.

```python
def run(args: dict) -> str:
    pattern = args.get("pattern")
    if pattern:
        return _load_format() + _load_pattern(pattern)
    return _load_format() + _load_all_patterns()
```

### Фаза 3: Мульти-паттерн (когда нужно)

Параметр `patterns` (массив) для запросов, смешивающих паттерны: "фильтруй пятницы с range > 200 и сгруппируй по месяцам" = filter_count + group_analysis.

## Формат паттерн-файла

```markdown
# Group Analysis

Grouping data by a column and computing aggregates.

## Key fields
- map: create the grouping column (dayofweek(), month(), etc.)
- group_by: column name (NOT a function — create in map first)
- select: aggregate function (mean, sum, count)
- sort: optional ordering

## Examples

Volume by weekday:
{"session": "RTH", "from": "daily", "map": {"weekday": "dayofweek()"},
 "group_by": "weekday", "select": "mean(volume)", "sort": "weekday asc"}

Range by month:
{"session": "RTH", "from": "daily", "map": {"range": "high - low", "m": "month()"},
 "group_by": "m", "select": "mean(range)", "sort": "m asc"}

## Common mistakes
- group_by: "dayofweek()" — WRONG. Create column in map first.
- Use == for comparison, not =
```

Каждый файл содержит: описание, ключевые поля, 2-3 примера, типичные ошибки.

## Добавление новой фичи

Когда добавляем бэктесты:
1. Создаём `patterns/backtest.md`
2. (Фаза 2+) Добавляем `"backtest"` в enum параметра

Промпт не растёт. Остальные паттерны не трогаем.

## Сравнение токенов (прогноз)

| Примеров | Сейчас (всё) | RAP (один паттерн) | Экономия |
|----------|-------------|-------------------|----------|
| 7        | ~500        | ~300              | 40%      |
| 15       | ~1000       | ~300              | 70%      |
| 30       | ~2000       | ~300              | 85%      |

## Файловая структура

```
assistant/tools/
  reference.py                 — tool declaration + run()
  reference/
    format.md                  — query format, always loaded
    patterns/
      simple_stat.md
      filter_count.md
      group_analysis.md
      pattern_detect.md
      ranking.md
```

## Риски

1. **Фаза 2: неправильный паттерн** — модель выберет не тот паттерн, получит не те примеры. Митигация: fallback без pattern = всё.
2. **Фаза 2: мульти-паттерн** — запрос смешивает паттерны. Митигация: Фаза 3 или fallback.
3. **Дрифт** — примеры в паттернах отстают от реального API. Митигация: тесты валидируют JSON в примерах.
