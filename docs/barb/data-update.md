# Data Auto-Update Architecture

## Overview

Автоматическое обновление рыночных данных. Cron на сервере скачивает новые бары с провайдера, append'ит к parquet файлам, сигналит API перечитать.

## Storage Structure

```
data/
  1d/
    futures/NQ.parquet     — daily bars (settlement close)
    stocks/AAPL.parquet    — (будущее)
  1m/
    futures/NQ.parquet     — minute bars
    stocks/AAPL.parquet    — (будущее)
```

Parquet: `[timestamp, open, high, low, close, volume]`, compression=zstd.

## Provider API

FirstRateData (`firstratedata.com/api`). Подписка per asset type.

Ключевое ограничение: **один zip со ВСЕМИ тикерами** данного типа. Нельзя запросить один тикер — получаешь все ~130 фьючерсов (или все ~10K акций) в одном архиве.

```
GET /api/last_update?type=futures          → "2026-02-10"
GET /api/data_file?type=futures&period=day&timeframe=1day&adjustment=contin_UNadj  → zip
GET /api/data_file?type=futures&period=day&timeframe=1min&adjustment=contin_UNadj  → zip
```

- `period=day` — данные за последний торговый день (готово в 1:00 AM ET)
- `period=full` — полный архив (готово в 2:00 AM ET)
- Ответ — zip с txt файлами, по одному на тикер

## Unit of Work = Asset Type

Asset type — естественная граница работы:
- API отдаёт данные per type (1 запрос = 1 тип = все тикеры)
- Разные расписания (крипто 24/7, фьючерсы/акции будни)
- Изоляция сбоев (stocks упал — futures работает)
- Подписка per type (добавляем по мере роста)

```
update_data.py --type futures
  → скачивает 2 zip (1day + 1min)
  → из ~130 тикеров берёт наши 31
  → append к parquet в data/{tf}/futures/

update_data.py --type stocks
  → скачивает 2 zip (1day + 1min)
  → из ~10000 тикеров берёт наши N
  → append к parquet в data/{tf}/stocks/
```

## Update Flow

```
1. GET last_update?type={type} → date
2. Сравнить с data/{type}/.last_update
3. Если нет нового — exit
4. GET period=day&timeframe=1day → zip → tmpdir/
5. GET period=day&timeframe=1min → zip → tmpdir/
6. Для каждого нашего тикера:
   a. read existing parquet (pandas)
   b. read new txt from zip
   c. concat + deduplicate by timestamp
   d. write parquet back (zstd)
7. Записать date → data/{type}/.last_update
8. POST /api/reload — сброс lru_cache
```

Дедупликация по timestamp защищает от двойного запуска.

## Symbol Mapping

Провайдер использует свои тикеры. Маппинг в скрипте:

```python
SYMBOL_MAP = {
    "A6": "6A",   "AD": "6C",   "B": "BRN",
    "B6": "6B",   "E1": "6S",   "E6": "6E",   "J1": "6J",
}
# Остальные совпадают: NQ, ES, CL, GC, ZN, ...
```

## Infrastructure

```yaml
# docker-compose.yml
services:
  api:
    # FastAPI — читает data/
    volumes:
      - ./data:/app/data:ro

  updater:
    # cron + update_data.py — пишет в data/
    volumes:
      - ./data:/app/data
```

Один updater контейнер, несколько cron entries:

```cron
15 1 * * 1-5  update_data.py --type futures
30 1 * * 1-5  update_data.py --type stocks
45 1 * * *    update_data.py --type crypto
```

Не нужны отдельные контейнеры per type — один скрипт с разными аргументами.

## Scale

| | Сейчас (31 futures) | Рост (10K+ mixed) |
|---|---|---|
| Тикеров | 31 из 130 | 10K+ |
| 1d download | ~1 MB zip | ~50 MB |
| 1m download | ~50 MB zip | гигабайты |
| Обработка | секунды | минуты per type |
| Cron entries | 1 | 3-5 |

## Reload Mechanism

После append данных — API должен сбросить `lru_cache` в `barb/data.py`.

Варианты:
1. **Restart контейнер** — просто, но даунтайм ~2 сек
2. **POST /api/reload** — endpoint вызывает `load_data.cache_clear()`, zero downtime
3. **File watcher** — сложно, не нужно

Начинаем с варианта 2 (reload endpoint).

## What We Don't Do (Yet)

- Партиционирование parquet по дате (не нужно при текущих размерах)
- Queue/worker система (overkill)
- Хранение всех тикеров провайдера (только наши)
- Custom continuous series from individual contracts (roadmap, см. data-pipeline.md)

Всё добавляется потом без слома текущей архитектуры.

## Files

```
scripts/update_data.py       — основной скрипт
scripts/convert_data.py      — начальная конвертация (txt → parquet, уже есть)
barb/data.py                 — load_data(instrument, timeframe, asset_type)
```
