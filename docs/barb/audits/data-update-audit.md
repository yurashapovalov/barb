# Audit: data-update.md

**Date**: 2026-02-16
**Claims checked**: 42
**Correct**: 36 | **Wrong**: 1 | **Outdated**: 0 | **Unverifiable**: 5

## Issues

### [WRONG] Cron example missing reload-data curl call
- **Doc says**: (line 119) cron is `15 6 * * 1-5 cd /opt/barb && .venv-scripts/bin/python scripts/update_data.py --type futures >> /var/log/barb-update.log 2>&1` and (line 156) "Cron вызывает после update_data.py" the reload endpoint
- **Code says**: The cron example does not include a `curl` call to `POST /api/admin/reload-data`. The update_data.py script itself has no reload call either. The doc claims cron calls reload after update_data.py but the shown cron line does not include it.
- **File**: `docs/barb/data-update.md:119,156`

### [UNVERIFIABLE] Actual cron schedule on server (Mon-Fri vs Mon-Sat)
- **Doc says**: (line 118) `Mon-Fri` with cron `1-5`
- **Note**: MEMORY.md says "Mon-Sat 6:15 UTC". The doc's cron syntax `1-5` is Mon-Fri. Cannot verify actual server crontab from codebase. The doc is internally consistent (`1-5` = Mon-Fri) but may not match actual server config.

### [UNVERIFIABLE] Provider data readiness times
- **Doc says**: (line 43-44) `period=day` ready at 1:00 AM ET, `period=full` ready at 2:00 AM ET
- **Note**: This is provider behavior, not verifiable from code

### [UNVERIFIABLE] Provider delivers ~130 futures in one zip
- **Doc says**: (line 34) "получаешь все ~130 фьючерсов"
- **Note**: Provider behavior, not verifiable from code

### [UNVERIFIABLE] Redirect goes to Backblaze B2
- **Doc says**: (line 45) "Ответ — redirect на Backblaze B2"
- **Note**: Provider infrastructure, not verifiable from code. Code does set `follow_redirects=True` (`scripts/update_data.py:281`)

### [UNVERIFIABLE] Server infrastructure details
- **Doc says**: (lines 111-114) Server at root@37.27.204.135, venv at /opt/barb/.venv-scripts/, log at /var/log/barb-update.log
- **Note**: Server config not verifiable from codebase. Matches MEMORY.md server address.

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Cron downloads new bars from provider, appends to parquet, updates Supabase | CORRECT | `scripts/update_data.py:main()` — downloads, processes, updates Supabase, writes state |
| 2 | Parquet files are cache, provider is source of truth | CORRECT | Design philosophy, `--period full --force` rebuilds from provider |
| 3 | Full rebuild via `--period full --force` | CORRECT | `scripts/update_data.py:248-253` — period choices include "full", force skips state check |
| 4 | Storage: `data/1d/futures/NQ.parquet` for daily bars | CORRECT | `data/1d/futures/NQ.parquet` exists on disk |
| 5 | Storage: `data/1m/futures/NQ.parquet` for minute bars | CORRECT | `data/1m/futures/NQ.parquet` exists on disk |
| 6 | State file at `data/futures/.last_update` | CORRECT | `scripts/update_data.py:278` — `DATA_DIR / asset_type / ".last_update"` = `data/futures/.last_update` |
| 7 | State file contains date string like "2026-02-12" | CORRECT | Actual file contains "2026-02-11" (same format) |
| 8 | Parquet columns: `[timestamp, open, high, low, close, volume]` | CORRECT | `scripts/update_data.py:91` — `KEEP_COLS = ["timestamp", "open", "high", "low", "close", "volume"]` |
| 9 | Compression is zstd | CORRECT | `scripts/update_data.py:195` — `compression="zstd"` |
| 10 | Daily CSV from provider has 7 columns including OI | CORRECT | `scripts/update_data.py:89` — `DAILY_COLS = ["timestamp", "open", "high", "low", "close", "volume", "oi"]` |
| 11 | OI dropped at parse time | CORRECT | `scripts/update_data.py:106` — `return df[KEEP_COLS]` (KEEP_COLS has no "oi") |
| 12 | Provider is FirstRateData at `firstratedata.com/api` | CORRECT | `scripts/update_data.py:27` — `API_BASE = "https://firstratedata.com/api"` |
| 13 | API endpoint: `GET /api/last_update?type=futures&userid={userid}` | CORRECT | `scripts/update_data.py:138-141` — exact params match |
| 14 | API endpoint: `GET /api/data_file?type=futures&period=day&timeframe=1day&adjustment=contin_UNadj&userid={userid}` | CORRECT | `scripts/update_data.py:160-168` — exact params match |
| 15 | `userid` hardcoded as `API_USERID` | CORRECT | `scripts/update_data.py:28` — `API_USERID = "XMbX1O2zD0--j0RfUK-W9A"` |
| 16 | Timeout 300s | CORRECT | `scripts/update_data.py:281` — `timeout=300` |
| 17 | Follows redirects | CORRECT | `scripts/update_data.py:281` — `follow_redirects=True` |
| 18 | Provider data readiness: 1:00 AM ET for day, 2:00 AM for full | UNVERIFIABLE | Provider behavior |
| 19 | Provider delivers ~130 futures in one zip | UNVERIFIABLE | Provider behavior |
| 20 | Redirect to Backblaze B2 | UNVERIFIABLE | Provider infra; code uses `follow_redirects=True` |
| 21 | Downloads 2 zips (1day + 1min) per type | CORRECT | `scripts/update_data.py:297` — loops over `TIMEFRAMES = {"1day": "1d", "1min": "1m"}` |
| 22 | From ~130 tickers takes our 31 | CORRECT | `scripts/update_data.py:47-81` — TARGET_TICKERS["futures"] has 31 entries |
| 23 | Atomic append to parquet in `data/{tf}/futures/` | CORRECT | `scripts/update_data.py:194-196` — writes .tmp then renames |
| 24 | Updates `data_end` in Supabase | CORRECT | `scripts/update_data.py:304` — calls `update_supabase_data_end()` |
| 25 | Update flow step 1: GET last_update | CORRECT | `scripts/update_data.py:283` |
| 26 | Update flow step 2: compare with local state | CORRECT | `scripts/update_data.py:284-288` |
| 27 | Update flow step 3: exit if no new data | CORRECT | `scripts/update_data.py:287-289` |
| 28 | Update flow step 6a: read existing parquet | CORRECT | `scripts/update_data.py:184` — `pd.read_parquet(existing_path)` |
| 29 | Update flow step 6b: parse new txt from zip | CORRECT | `scripts/update_data.py:232` — calls parser on zip data |
| 30 | Update flow step 6c: concat + deduplicate by timestamp | CORRECT | `scripts/update_data.py:186-187` — `pd.concat` + `drop_duplicates(subset=["timestamp"])` |
| 31 | Update flow step 6e: write .tmp then rename (atomic) | CORRECT | `scripts/update_data.py:194-196` |
| 32 | Update flow step 7: PATCH Supabase instruments.data_end | CORRECT | `scripts/update_data.py:122-131` — PATCH to `/rest/v1/instruments?type=eq.{asset_type}` |
| 33 | Update flow step 8: write date to state file | CORRECT | `scripts/update_data.py:307` — `write_state(state_path, remote_date)` |
| 34 | SYMBOL_MAP has 7 entries matching code | CORRECT | `scripts/update_data.py:36-44` — identical 7 mappings |
| 35 | Supabase credentials from `.env` (SUPABASE_URL, SUPABASE_SERVICE_KEY) | CORRECT | `scripts/update_data.py:30-31` — `os.environ.get("SUPABASE_URL")` and `os.environ.get("SUPABASE_SERVICE_KEY")` |
| 36 | Server at root@37.27.204.135 (/opt/barb) | UNVERIFIABLE | Server config |
| 37 | Cron at 6:15 UTC Mon-Fri | WRONG | Doc shows `1-5` (Mon-Fri) but MEMORY.md says Mon-Sat. Actual crontab unverifiable. See Issues. |
| 38 | `POST /api/admin/reload-data?token=ADMIN_TOKEN` clears both caches | CORRECT | `api/main.py:370-377` — `load_data.cache_clear()` + `_get_assistant.cache_clear()` |
| 39 | Cron calls reload-data after update_data.py | WRONG | Cron example in doc has no curl/reload call; update_data.py has no reload call. See Issues. |
| 40 | CLI: `--type`, `--dry-run`, `--force`, `--period` flags exist | CORRECT | `scripts/update_data.py:247-263` — all four flags defined |
| 41 | Files: `scripts/update_data.py`, `scripts/convert_data.py`, `barb/data.py` all exist | CORRECT | All three files verified on disk |
| 42 | `load_data(instrument, timeframe, asset_type)` signature | CORRECT | `barb/data.py:12` — `load_data(instrument: str, timeframe: str = "1d", asset_type: str = "futures")` |
