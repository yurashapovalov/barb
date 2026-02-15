# Audit: data-update.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 14: "data/1d/futures/NQ.parquet -- daily bars (settlement close)"
- **Verdict**: ACCURATE
- **Evidence**: file exists; `scripts/update_data.py:86` — `TIMEFRAMES = {"1day": "1d", ...}`

### Claim 2
- **Doc**: line 19: "data/1m/futures/NQ.parquet -- minute bars"
- **Verdict**: ACCURATE
- **Evidence**: file exists; `scripts/update_data.py:87` — `"1min": "1m"`

### Claim 3
- **Doc**: line 22: "data/futures/.last_update -- state file"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:278` — `state_path = DATA_DIR / asset_type / ".last_update"`

### Claim 4
- **Doc**: line 26: "Parquet: [timestamp, open, high, low, close, volume], compression=zstd"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:91` — `KEEP_COLS`; line 195 — `compression="zstd"`

### Claim 5
- **Doc**: line 32: "FirstRateData (firstratedata.com/api)"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:27` — `API_BASE = "https://firstratedata.com/api"`

### Claim 6
- **Doc**: line 34: "один zip со ВСЕМИ тикерами"
- **Verdict**: UNVERIFIABLE
- **Evidence**: external API behavior

### Claim 7
- **Doc**: line 37: "GET /api/last_update?type=futures"
- **Verdict**: WRONG
- **Evidence**: `scripts/update_data.py:139-141` — also requires `userid` parameter
- **Fix**: add `&userid={userid}`

### Claim 8
- **Doc**: line 38: "GET /api/data_file?type=futures&period=day&timeframe=1day&adjustment=contin_UNadj"
- **Verdict**: WRONG
- **Evidence**: `scripts/update_data.py:162-168` — also requires `userid` parameter
- **Fix**: add `&userid={userid}`

### Claim 9
- **Doc**: lines 102-105: SYMBOL_MAP entries
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:36-44` — identical mapping

### Claim 10
- **Doc**: line 57: "из ~130 тикеров берёт наши 31"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:47-81` — 31 tickers

### Claim 11
- **Doc**: line 56: "скачивает 2 zip (1day + 1min)"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:84-87,297-298`

### Claim 12
- **Doc**: line 58: "atomic append к parquet"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:194-196` — `.parquet.tmp` then `rename()`

### Claim 13
- **Doc**: line 59: "обновляет data_end в Supabase"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:304`

### Claim 14
- **Doc**: line 68: "GET last_update -> date" (step 1)
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:138-143`

### Claim 15
- **Doc**: line 69: "Сравнить с .last_update" (step 2)
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:284-287`

### Claim 16
- **Doc**: line 70: "Если нет нового -- exit" (step 3)
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:287-289`

### Claim 17
- **Doc**: line 76: "validate new data (timestamps, OHLC > 0, no NaN)"
- **Verdict**: WRONG
- **Evidence**: `scripts/update_data.py:175-243` — no such validation exists, only empty-data checks
- **Fix**: remove claim or implement validation in code

### Claim 18
- **Doc**: line 77: "concat + deduplicate by timestamp"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:186-187` — `drop_duplicates(subset=["timestamp"])`

### Claim 19
- **Doc**: line 78: "write to .tmp file -> rename (atomic)"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:194-196`

### Claim 20
- **Doc**: line 79: "PATCH Supabase instruments.data_end" (step 7)
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:122-130`

### Claim 21
- **Doc**: line 80: "Записать date -> .last_update" (step 8)
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:307`

### Claim 22
- **Doc**: line 85: "Write to .tmp, then rename()"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:194-196`

### Claim 23
- **Doc**: lines 88-89: "timestamps > last existing, OHLC > 0, no NaN"
- **Verdict**: WRONG
- **Evidence**: none of these checks exist in code
- **Fix**: remove claims or implement validation

### Claim 24
- **Doc**: line 90: "Expected columns present"
- **Verdict**: WRONG
- **Evidence**: no column validation in code
- **Fix**: remove claim or implement validation

### Claim 25
- **Doc**: line 91: "Non-empty data"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:229-234` — skips empty files

### Claim 26
- **Doc**: line 93: "дедупликация по timestamp, повторный запуск безопасен"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:187`

### Claim 27
- **Doc**: line 143: "Credentials из .env (SUPABASE_URL, SUPABASE_SERVICE_KEY)"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:25,30-31`

### Claim 28
- **Doc**: line 139: "PATCH /rest/v1/instruments"
- **Verdict**: ACCURATE
- **Evidence**: `scripts/update_data.py:123`

### Claim 29
- **Doc**: line 157: "API должен сбросить lru_cache"
- **Verdict**: ACCURATE
- **Evidence**: `barb/data.py:11` — `@lru_cache`; `api/main.py:376` — `cache_clear()`

### Claim 30
- **Doc**: line 161: "POST /api/reload"
- **Verdict**: WRONG
- **Evidence**: `api/main.py:370` — actual endpoint is `POST /api/admin/reload-data`
- **Fix**: change to `POST /api/admin/reload-data`

### Claim 31
- **Doc**: line 163: "Начинаем с варианта 2 (reload endpoint). TODO."
- **Verdict**: OUTDATED
- **Evidence**: `api/main.py:370-378` — already implemented with admin token auth
- **Fix**: remove "TODO"

### Claims 32-35
- **Doc**: CLI commands (--type, --dry-run, --force, --period full)
- **Verdict**: ACCURATE
- **Evidence**: all verified in `scripts/update_data.py:247-263`

### Claims 36-38
- **Doc**: File descriptions (update_data.py, convert_data.py, data.py)
- **Verdict**: ACCURATE
- **Evidence**: all files exist and match descriptions

### Claims 39-41
- **Doc**: Server paths (venv, log, server address)
- **Verdict**: UNVERIFIABLE
- **Evidence**: server filesystem, cannot verify locally

### Claim 42
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `scripts/update_data.py:28` — hardcoded `API_USERID`
- **Fix**: add to "Provider API" section

### Claim 43
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `scripts/update_data.py:158,281` — Backblaze B2 redirect + 300s timeout
- **Fix**: add to "Provider API" section

### Claim 44
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `scripts/update_data.py:89-91` — OI column parsed then dropped
- **Fix**: add to "Storage Structure" section

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 26 |
| OUTDATED | 1 |
| WRONG | 5 |
| MISSING | 3 |
| UNVERIFIABLE | 3 |
| **Total** | **38** |
| **Accuracy** | **68%** |

## Verification

Date: 2026-02-15

### Claim 1 — CONFIRMED
### Claim 2 — CONFIRMED
### Claim 3 — CONFIRMED
### Claim 4 — CONFIRMED
### Claim 5 — CONFIRMED
### Claim 6 — INCONCLUSIVE
- **Reason**: external API behavior
### Claim 7 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: OUTDATED (incomplete)
- **Reason**: endpoint IS correct, just missing `userid` parameter. Incomplete, not wrong.
### Claim 8 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: OUTDATED (incomplete)
- **Reason**: same as Claim 7 — URL missing userid parameter
### Claim 9 — CONFIRMED
### Claim 10 — CONFIRMED
### Claim 11 — CONFIRMED
### Claim 12 — CONFIRMED
### Claim 13 — CONFIRMED
### Claim 14 — CONFIRMED
### Claim 15 — CONFIRMED
### Claim 16 — CONFIRMED
### Claim 17 — CONFIRMED
### Claim 18 — CONFIRMED
### Claim 19 — CONFIRMED
### Claim 20 — CONFIRMED
### Claim 21 — CONFIRMED
### Claim 22 — CONFIRMED
### Claim 23 — CONFIRMED
### Claim 24 — CONFIRMED
### Claim 25 — CONFIRMED
### Claim 26 — CONFIRMED
### Claim 27 — CONFIRMED
### Claim 28 — CONFIRMED
### Claim 29 — CONFIRMED
### Claim 30 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: WRONG (confirmed, verdict correct but noted)
### Claim 31 — CONFIRMED
### Claims 32-35 — CONFIRMED
### Claims 36-38 — CONFIRMED
### Claims 39-41 — INCONCLUSIVE
- **Reason**: server filesystem paths
### Claim 42 — CONFIRMED
### Claim 43 — CONFIRMED
### Claim 44 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 35 |
| DISPUTED | 3 |
| INCONCLUSIVE | 3 |
| **Total** | **41** |
