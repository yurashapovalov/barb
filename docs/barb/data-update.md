# Data Auto-Update Architecture

## Overview

Автоматическое обновление рыночных данных. Cron на сервере скачивает новые бары с провайдера, append'ит к parquet файлам, обновляет Supabase.

## Key Principle: Parquet = Cache

Parquet файлы — кеш, не база данных. Source of truth — провайдер (18 лет истории). Полный rebuild за 30 минут: `--period full --force`. Бэкапить кеш не нужно — нужно не ломать его и быстро детектить проблемы.

## Storage Structure

```
data/
  1d/
    futures/NQ.parquet     — daily bars (settlement close)
    stocks/AAPL.parquet    — (будущее)
  1m/
    futures/NQ.parquet     — minute bars
    stocks/AAPL.parquet    — (будущее)
  futures/
    .last_update           — "2026-02-12" (state file, per asset type)
  stocks/                  — (будущее)
```

Parquet: `[timestamp, open, high, low, close, volume]`, compression=zstd. Daily CSV from provider has 7 columns (includes OI) — OI dropped at parse time.

Parquet — бинарный файл, не база данных. Нет транзакций, нет partial update, нет concurrent access. Добавить строку = перезаписать весь файл. Если процесс упал mid-write — файл corrupt.

## Provider API

FirstRateData (`firstratedata.com/api`). Подписка per asset type.

Ключевое ограничение: **один zip со ВСЕМИ тикерами** данного типа. Нельзя запросить один тикер — получаешь все ~130 фьючерсов (или все ~10K акций) в одном архиве.

```
GET /api/last_update?type=futures&userid={userid}          → "2026-02-10"
GET /api/data_file?type=futures&period=day&timeframe=1day&adjustment=contin_UNadj&userid={userid}  → zip
GET /api/data_file?type=futures&period=day&timeframe=1min&adjustment=contin_UNadj&userid={userid}  → zip
```

- `userid` — hardcoded в скрипте (`API_USERID`)
- `period=day` — данные за последний торговый день (готово в 1:00 AM ET)
- `period=full` — полный архив (готово в 2:00 AM ET)
- Ответ — redirect на Backblaze B2 → zip с txt файлами, по одному на тикер (timeout 300s)

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
  → валидация → atomic append к parquet в data/{tf}/futures/
  → обновляет data_end в Supabase

update_data.py --type stocks (будущее)
  → то же самое для data/{tf}/stocks/
```

## Update Flow

```
1. GET last_update?type={type} → date
2. Сравнить с data/{type}/.last_update
3. Если нет нового — exit
4. GET period=day&timeframe=1day → zip
5. GET period=day&timeframe=1min → zip
6. Для каждого нашего тикера:
   a. read existing parquet (pandas)
   b. parse new txt from zip
   c. concat + deduplicate by timestamp
   e. write to .tmp file → rename (atomic)
7. PATCH Supabase instruments.data_end
8. Записать date → data/{type}/.last_update
```

### Data Safety

**Атомарная запись** — самая важная защита. Write to `NQ.parquet.tmp`, then `rename()` to `NQ.parquet`. `rename()` атомарен на уровне ФС. Crash mid-write не повреждает оригинал.

**Валидация перед записью:**
- Non-empty data (пропускает пустые файлы)

**Идемпотентность** — дедупликация по timestamp, повторный запуск безопасен.

**Recovery** — если данные corrupt: `--period full --force` перекачивает всё с нуля (~30 мин).

## Symbol Mapping

Провайдер использует свои тикеры. Маппинг в скрипте:

```python
SYMBOL_MAP = {
    "A6": "6A",   "AD": "6C",   "B": "BRN",
    "B6": "6B",   "E1": "6S",   "E6": "6E",   "J1": "6J",
}
# Остальные совпадают: NQ, ES, CL, GC, ZN, ...
```

## Infrastructure (текущее)

Скрипт на хосте, venv для зависимостей, cron:

```
Server: root@37.27.204.135 (/opt/barb)
Venv:   /opt/barb/.venv-scripts/ (pandas, httpx, python-dotenv, pyarrow)
Log:    /var/log/barb-update.log
State:  data/{type}/.last_update (e.g. data/futures/.last_update)
```

```cron
# 1:15 AM ET (6:15 UTC), Mon-Fri
15 6 * * 1-5 cd /opt/barb && .venv-scripts/bin/python scripts/update_data.py --type futures >> /var/log/barb-update.log 2>&1
```

При росте:
```cron
15 6 * * 1-5  update_data.py --type futures
30 6 * * 1-5  update_data.py --type stocks
45 6 * * *    update_data.py --type crypto
```

Не нужны отдельные контейнеры per type — один скрипт с разными аргументами.

## Supabase Integration

После успешного append скрипт обновляет `data_end` для всех инструментов данного типа:

```
PATCH /rest/v1/instruments?type=eq.futures
{"data_end": "2026-02-10"}
```

Credentials из `.env` (SUPABASE_URL, SUPABASE_SERVICE_KEY).

## Scale

| | Сейчас (31 futures) | Рост (10K+ mixed) |
|---|---|---|
| Тикеров | 31 из 130 | 10K+ |
| 1d download | ~1 MB zip | ~50 MB |
| 1m download | ~1.3 MB (period=day) | гигабайты |
| Обработка | ~15 сек | минуты per type |
| Cron entries | 1 | 3-5 |

## Reload Mechanism

После append данных — API должен сбросить `lru_cache` в `barb/data.py`.

`POST /api/admin/reload-data?token=ADMIN_TOKEN` — вызывает `load_data.cache_clear()` + `_get_assistant.cache_clear()`, zero downtime. Cron вызывает после update_data.py.

## CLI

```bash
# Обычный ежедневный апдейт
update_data.py --type futures

# Проверить есть ли новое (без скачивания)
update_data.py --type futures --dry-run

# Принудительно перекачать (игнорировать state)
update_data.py --type futures --force

# Полный rebuild с нуля
update_data.py --type futures --period full --force
```

## What We Don't Do (Yet)

- Бэкап parquets (провайдер — это бэкап, rebuild за 30 мин)
- Партиционирование parquet по дате (не нужно при текущих размерах)
- Queue/worker система (overkill)
- Хранение всех тикеров провайдера (только наши)
- Custom continuous series from individual contracts (roadmap, см. data-pipeline.md)
- Мониторинг/алерты (webhook в Telegram при ошибке — TODO)

## Files

```
scripts/update_data.py       — ежедневный апдейт (cron)
scripts/convert_data.py      — начальная конвертация (txt → parquet, разовая)
barb/data.py                 — load_data(instrument, timeframe, asset_type)
```
