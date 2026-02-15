# Audit: infrastructure.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 6: "GitHub (yurashapovalov/barb)"
- **Verdict**: UNVERIFIABLE
- **Evidence**: remote repository name, cannot verify from local code

### Claim 2
- **Doc**: line 8: "GitHub Actions -> тесты + деплой бэкенда на Hetzner"
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:8-41` — test job + deploy job SSHs to 37.27.204.135

### Claim 3
- **Doc**: line 9: "Vercel -> автодеплой фронта"
- **Verdict**: UNVERIFIABLE
- **Evidence**: `front/vercel.json` exists but Vercel deployment is external

### Claim 4
- **Doc**: line 12: "Бэкенд (Hetzner, 37.27.204.135)"
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:35` — `host: 37.27.204.135`

### Claim 5
- **Doc**: line 14: "Docker Compose: docker-compose.yml + docker-compose.prod.yml"
- **Verdict**: ACCURATE
- **Evidence**: both files exist; `.github/workflows/deploy.yml:41` uses both

### Claim 6
- **Doc**: line 15: "Uvicorn, 2 воркера"
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:12` — `--workers 2`

### Claim 7
- **Doc**: line 16: "Данные (Parquet) в volume /app/data"
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:14` — `./data:/app/data`

### Claim 8
- **Doc**: line 17: "Деплой: SSH -> git pull -> docker compose up --build"
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:38-41`

### Claim 9
- **Doc**: line 20: "Root directory: front/"
- **Verdict**: UNVERIFIABLE
- **Evidence**: Vercel root directory configured in dashboard, not in code

### Claim 10
- **Doc**: line 21: "Build: npm run build -> dist/"
- **Verdict**: ACCURATE
- **Evidence**: `front/package.json:8` — `"build": "tsc -b && vite build"`

### Claim 11
- **Doc**: line 22: "SPA rewrite: vercel.json"
- **Verdict**: ACCURATE
- **Evidence**: `front/vercel.json:3` — rewrite rule to index.html

### Claim 12
- **Doc**: line 27: "getbarb.trade -> Vercel (фронт)"
- **Verdict**: UNVERIFIABLE
- **Evidence**: DNS configuration is external

### Claim 13
- **Doc**: line 28: "api.getbarb.trade -> 37.27.204.135"
- **Verdict**: UNVERIFIABLE
- **Evidence**: `Caddyfile:1` references `api.getbarb.trade` but DNS is external

### Claim 14
- **Doc**: line 32: "Файл: .github/workflows/deploy.yml"
- **Verdict**: ACCURATE
- **Evidence**: file exists

### Claim 15
- **Doc**: line 34: "test -- pip install -> ruff check -> pytest"
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:20-26`

### Claim 16
- **Doc**: line 35: "deploy -- SSH -> git pull -> docker compose up"
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:32-41`

### Claim 17
- **Doc**: line 37: "Deploy запускается только после успешных тестов"
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:29` — `needs: test`

### Claim 18
- **Doc**: line 42: "CORS: https://getbarb.trade"
- **Verdict**: WRONG
- **Evidence**: `docker-compose.prod.yml:7` — default includes `https://getbarb.trade,http://localhost:3000`
- **Fix**: add `,http://localhost:3000` to CORS value

### Claim 19
- **Doc**: line 43: "ENV: production"
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:6` — `ENV=production`

### Claim 20
- **Doc**: line 44: "Логи: JSON формат"
- **Verdict**: ACCURATE
- **Evidence**: `api/main.py:30-46` — `_JSONFormatter` in production

### Claim 21
- **Doc**: line 45: "2 uvicorn воркера"
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:12` — `--workers 2`

### Claim 22
- **Doc**: line 48: "CORS: *"
- **Verdict**: ACCURATE
- **Evidence**: `api/main.py:76` — defaults to `"*"`

### Claim 23
- **Doc**: line 49: "ENV: development"
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.yml:19` — `ENV=development`

### Claim 24
- **Doc**: line 50: "Логи: plaintext"
- **Verdict**: ACCURATE
- **Evidence**: `api/main.py:48-52` — `logging.basicConfig` with text format

### Claim 25
- **Doc**: line 51: "Hot-reload через volume mounts"
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.yml:7-11` — mounts all source dirs; line 20 — `--reload`

### Claim 26
- **Doc**: line 52: "Все исходники монтируются в контейнер"
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.yml:7-11` — data, barb, assistant, api, config mounted

### Claim 27
- **Doc**: line 56: "ANTHROPIC_API_KEY"
- **Verdict**: ACCURATE
- **Evidence**: `api/config.py:9` — `anthropic_api_key: str`

### Claim 28
- **Doc**: line 57: "SUPABASE_ANON_KEY -- backend secret"
- **Verdict**: OUTDATED
- **Evidence**: `api/config.py` has no `supabase_anon_key`; only frontend uses it
- **Fix**: remove from backend secrets, note as frontend-only

### Claim 29
- **Doc**: line 58: "SUPABASE_JWT_SECRET -- валидация JWT"
- **Verdict**: WRONG
- **Evidence**: `api/auth.py:15` — uses JWKS endpoint with ES256, not JWT_SECRET. Not in `api/config.py`.
- **Fix**: remove entirely — JWT validation uses JWKS, not a secret

### Claim 30
- **Doc**: line 59: "VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/lib/supabase.ts:3,6` and `front/src/lib/api.ts:16`

### Claim 31
- **Doc**: line 60: "SSH_PRIVATE_KEY -- GitHub Actions"
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:37` — `key: ${{ secrets.SSH_PRIVATE_KEY }}`

### Claim 32
- **Doc**: line 64: "Три таблицы: conversations, messages, tool_calls"
- **Verdict**: OUTDATED
- **Evidence**: migrations show 6 tables: +instruments, exchanges, user_instruments
- **Fix**: change to "Шесть таблиц" and list all

### Claim 33
- **Doc**: line 64: "RLS -- пользователь видит только свои данные"
- **Verdict**: ACCURATE
- **Evidence**: RLS policies with `auth.uid() = user_id` on all user-scoped tables

### Claim 34
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `Caddyfile:1-3` and `docker-compose.prod.yml:16-25` — Caddy reverse proxy with TLS
- **Fix**: add Caddy to "Бэкенд" section

### Claim 35
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `docker-compose.yml:14` — `GEMINI_API_KEY` env var
- **Fix**: add to "Секреты"

### Claim 36
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `api/config.py:12` — `ADMIN_TOKEN` for reload-data endpoint
- **Fix**: add to "Секреты"

### Claim 37
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `supabase/migrations/20260214_instrument_full_view.sql` — `instrument_full` view
- **Fix**: add to "База данных"

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 21 |
| OUTDATED | 2 |
| WRONG | 2 |
| MISSING | 4 |
| UNVERIFIABLE | 4 |
| **Total** | **33** |
| **Accuracy** | **64%** |

## Verification

Date: 2026-02-15

### Claim 1 — CONFIRMED
### Claim 2 — CONFIRMED
### Claim 3 — CONFIRMED
### Claim 4 — CONFIRMED
### Claim 5 — CONFIRMED
### Claim 6 — CONFIRMED
### Claim 7 — CONFIRMED
### Claim 8 — CONFIRMED
### Claim 9 — CONFIRMED
### Claim 10 — CONFIRMED
### Claim 11 — CONFIRMED
### Claim 12 — CONFIRMED
### Claim 13 — CONFIRMED
### Claim 14 — CONFIRMED
### Claim 15 — CONFIRMED
### Claim 16 — CONFIRMED
### Claim 17 — CONFIRMED
### Claim 18 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: OUTDATED (incomplete)
- **Reason**: doc lists primary CORS origin `https://getbarb.trade`, omits `http://localhost:3000` fallback. Incomplete, not wrong.
### Claim 19 — CONFIRMED
### Claim 20 — CONFIRMED
### Claim 21 — CONFIRMED
### Claim 22 — CONFIRMED
### Claim 23 — CONFIRMED
### Claim 24 — CONFIRMED
### Claim 25 — CONFIRMED
### Claim 26 — CONFIRMED
### Claim 27 — CONFIRMED
### Claim 28 — DISPUTED
- **Auditor said**: OUTDATED
- **Should be**: WRONG
- **Reason**: SUPABASE_ANON_KEY is not a backend secret at all (frontend-only). Not outdated — it was never correct.
### Claim 29 — CONFIRMED
### Claim 30 — CONFIRMED
### Claim 31 — CONFIRMED
### Claim 32 — CONFIRMED
### Claim 33 — CONFIRMED
### Claim 34 — CONFIRMED
### Claim 35 — CONFIRMED
### Claim 36 — DISPUTED
- **Auditor said**: MISSING
- **Should be**: INCONCLUSIVE
- **Reason**: ADMIN_TOKEN is dev-only (not in docker-compose.prod.yml). Doc's "Секреты" may intentionally list only production secrets.
### Claim 37 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 34 |
| DISPUTED | 3 |
| INCONCLUSIVE | 0 |
| **Total** | **37** |
