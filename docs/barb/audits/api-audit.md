# Audit: api.md

Date: 2026-02-15

## Claims

### Claims 1-7, 9-14, 16-25, 28-31
- **Verdict**: ACCURATE
- **Evidence**: All documented endpoints (health, conversations CRUD, chat/stream), SSE events (title_update, text_delta, tool_start, tool_end, done, persist), request flow steps 1-7, lru_cache caching, development plaintext logging, per-request logging — all verified against code

### Claim 8
- **Doc**: line 21: "JWT validation uses SUPABASE_JWT_SECRET with HS256"
- **Verdict**: WRONG
- **Evidence**: `api/auth.py:15-16` — uses JWKS endpoint: `PyJWKClient(f"{...}/auth/v1/.well-known/jwks.json")`; line 36 — `algorithms=["ES256"]`
- **Fix**: change to "JWKS endpoint (ES256, audience='authenticated')"

### Claim 15
- **Doc**: line 42: "data_block SSE event: {result, rows, title}"
- **Verdict**: OUTDATED
- **Evidence**: `assistant/chat.py:199-206` — also includes `tool`, `input`, `chart`
- **Fix**: add missing fields

### Claim 26
- **Doc**: line 68: "Один Assistant = один anthropic.Client + загруженный DataFrame"
- **Verdict**: OUTDATED
- **Evidence**: `assistant/chat.py:26-39` — stores two DataFrames (`df_daily` and `df_minute`)
- **Fix**: change to "два DataFrame (daily + minute)"

### Claim 27
- **Doc**: line 72: "JSON log format: (ts, level, logger, msg)"
- **Verdict**: OUTDATED
- **Evidence**: `api/main.py:34-41` — also includes `request_id`
- **Fix**: add `request_id` to format

### Claim 32
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `api/main.py:325` — `GET /api/instruments` endpoint
- **Fix**: add to endpoints section

### Claim 33
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `api/main.py:347` — `GET /api/instruments/{symbol}/ohlc` endpoint
- **Fix**: add to endpoints section

### Claim 34
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `api/main.py:370` — `POST /api/admin/reload-data` endpoint
- **Fix**: add to endpoints section

### Claim 35
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `api/main.py:381-456` — `GET/POST/DELETE /api/user-instruments` endpoints
- **Fix**: add to endpoints section

### Claim 36
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `assistant/chat.py` — SSE `error` event on stream failures
- **Fix**: add to SSE events section

### Claim 37
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `api/main.py` — `_maybe_summarize()` context summarization step after persist
- **Fix**: add to request flow

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 21 |
| OUTDATED | 3 |
| WRONG | 1 |
| MISSING | 6 |
| UNVERIFIABLE | 0 |
| **Total** | **31** |
| **Accuracy** | **68%** |

## Verification

Date: 2026-02-15

### Claims 1-7, 9-14, 16-25, 28-31 — CONFIRMED
### Claim 8 — CONFIRMED
### Claim 15 — CONFIRMED
### Claim 26 — CONFIRMED
### Claim 27 — CONFIRMED
### Claims 32-37 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 37 |
| DISPUTED | 0 |
| INCONCLUSIVE | 0 |
| **Total** | **37** |
