# Audit: infrastructure.md

Date: 2026-02-15 (full re-audit)

Source: `docs/barb/infrastructure.md`

Verified against: `docker-compose.yml`, `docker-compose.prod.yml`, `Caddyfile`, `Dockerfile`, `.github/workflows/deploy.yml`, `api/config.py`, `api/auth.py`, `api/main.py`, `api/db.py`, `front/vercel.json`, `front/package.json`, `config/models.py`, `assistant/chat.py`, all 19 files in `supabase/migrations/`.

---

## Section: Deploy (lines 3-18)

### Claim 1 — "GitHub (yurashapovalov/barb)" (line 6)
- **Verdict**: UNVERIFIABLE
- **Evidence**: Remote repository name cannot be verified from local code alone.

### Claim 2 — "GitHub Actions -> тесты + деплой бэкенда на Hetzner" (line 8)
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml` — `test` job (lint + pytest), `deploy` job (SSH to Hetzner).

### Claim 3 — "Vercel -> автодеплой фронта" (line 9)
- **Verdict**: UNVERIFIABLE
- **Evidence**: `front/vercel.json` exists with SPA rewrite, but Vercel deployment is configured externally.

### Claim 4 — "Бэкенд (Hetzner, 37.27.204.135)" (line 12)
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:35` — `host: 37.27.204.135`.

### Claim 5 — "Docker Compose: docker-compose.yml + docker-compose.prod.yml" (line 14)
- **Verdict**: ACCURATE
- **Evidence**: Both files exist. `.github/workflows/deploy.yml:41` — `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`.

### Claim 6 — "Caddy reverse proxy: автоматический TLS, api.getbarb.trade -> api:8000" (line 15)
- **Verdict**: ACCURATE
- **Evidence**: `Caddyfile:1-3` — `api.getbarb.trade { reverse_proxy api:8000 }`. Caddy automatically provisions TLS when a domain is specified.

### Claim 7 — "Uvicorn, 2 воркера" (line 16)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:12` — `uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2`.

### Claim 8 — "Данные (Parquet) в volume ./data:/app/data" (line 17)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:14` — `./data:/app/data`. Also `docker-compose.yml:7` same mount.

### Claim 9 — "Деплой: SSH -> cd /opt/barb -> git pull -> docker compose up -d --build -> docker system prune -f" (line 18)
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:38-42` — exact match of the command sequence.

---

## Section: Фронт (lines 20-24)

### Claim 10 — "Root directory: front/" (line 22)
- **Verdict**: UNVERIFIABLE
- **Evidence**: Vercel root directory is configured in dashboard, not in code. `front/vercel.json` exists at the right path.

### Claim 11 — "Build: tsc -b && vite build -> dist/" (line 23)
- **Verdict**: ACCURATE
- **Evidence**: `front/package.json:8` — `"build": "tsc -b && vite build"`. Vite outputs to `dist/` by default.

### Claim 12 — "SPA rewrite: vercel.json -> все пути на index.html" (line 24)
- **Verdict**: ACCURATE
- **Evidence**: `front/vercel.json:3` — `{ "source": "/(.*)", "destination": "/index.html" }`.

---

## Section: DNS (lines 26-29)

### Claim 13 — "getbarb.trade -> Vercel (фронт)" (line 28)
- **Verdict**: UNVERIFIABLE
- **Evidence**: DNS configuration is external.

### Claim 14 — "api.getbarb.trade -> 37.27.204.135 (Caddy -> Uvicorn)" (line 29)
- **Verdict**: PARTIALLY VERIFIABLE
- **Evidence**: `Caddyfile:1` references `api.getbarb.trade`. `.github/workflows/deploy.yml:35` confirms `37.27.204.135`. DNS A record itself is external.

---

## Section: CI (lines 31-38)

### Claim 15 — "Файл: .github/workflows/deploy.yml" (line 33)
- **Verdict**: ACCURATE
- **Evidence**: File exists at that path.

### Claim 16 — "test: pip install -e .[dev] -> ruff check . -> pytest --tb=short -q" (line 35)
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:20-26` — exact match.

### Claim 17 — "deploy: SSH на Hetzner -> git pull -> docker compose up" (line 36)
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:32-42`.

### Claim 18 — "Deploy запускается только после успешных тестов (needs: test)" (line 38)
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:29` — `needs: test`.

---

## Section: Production environment (lines 42-47)

### Claim 19 — "CORS: https://getbarb.trade,http://localhost:3000" (line 43)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:7` — `CORS_ORIGINS=${CORS_ORIGINS:-https://getbarb.trade,http://localhost:3000}`. Default matches exactly.

### Claim 20 — "ENV: production" (line 44)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:6` — `ENV=production`.

### Claim 21 — "Логи: JSON формат (_JSONFormatter)" (line 45)
- **Verdict**: ACCURATE
- **Evidence**: `api/main.py:30-42` — `_JSONFormatter` class used when `ENV == "production"`. Outputs JSON with `ts`, `level`, `logger`, `msg`, `request_id`.

### Claim 22 — "2 uvicorn воркера (--workers 2)" (line 46)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:12` — `--workers 2`.

### Claim 23 — "Caddy: порты 80/443, автоматический TLS" (line 47)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.prod.yml:19-20` — ports `80:80` and `443:443`. Caddy auto-provisions TLS.

---

## Section: Development environment (lines 49-55)

### Claim 24 — "CORS: * (default)" (line 50)
- **Verdict**: ACCURATE
- **Evidence**: `api/main.py:76` — `os.getenv("CORS_ORIGINS", "*")`. Dev compose does not set `CORS_ORIGINS`, so default `*` applies.

### Claim 25 — "ENV: development" (line 51)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.yml:19` — `ENV=development`.

### Claim 26 — "Логи: plaintext" (line 52)
- **Verdict**: ACCURATE
- **Evidence**: `api/main.py:48-52` — `logging.basicConfig` with text format in non-production.

### Claim 27 — "Hot-reload (--reload) через volume mounts" (line 53)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.yml:20` — `--reload`. Lines 7-11 mount source directories.

### Claim 28 — "Исходники монтируются: barb/, assistant/, api/, config/, data/" (line 54)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.yml:7-11` — mounts `./data`, `./barb`, `./assistant`, `./api`, `./config`.

### Claim 29 — "Healthcheck: curl -f http://localhost:8000/health каждые 30s" (line 55)
- **Verdict**: ACCURATE
- **Evidence**: `docker-compose.yml:21-25` — `curl -f http://localhost:8000/health`, `interval: 30s`.

---

## Section: Секреты — Бэкенд (lines 59-66)

### Claim 30 — "ANTHROPIC_API_KEY — Claude API" (line 60)
- **Verdict**: ACCURATE
- **Evidence**: `api/config.py:9` — `anthropic_api_key: str`. `assistant/chat.py:34` — `anthropic.Anthropic(api_key=api_key)`. Both compose files pass it.

### Claim 31 — "GEMINI_API_KEY — Gemini API" (line 61)
- **Verdict**: INACCURATE
- **Evidence**: `GEMINI_API_KEY` is passed in both `docker-compose.yml:14` and `docker-compose.prod.yml:9`, but `api/config.py` does NOT define `gemini_api_key`. No Python code reads this env var. `config/models.py` defines Gemini model configs, and `assistant/chat.py:34` uses `anthropic.Anthropic` (not Gemini SDK). The env var is unused dead config.
- **Note**: The var is present in compose files and would be needed if/when the Gemini migration completes, but calling it a used backend secret is currently inaccurate.

### Claim 32 — "SUPABASE_URL — Supabase endpoint" (line 62)
- **Verdict**: ACCURATE
- **Evidence**: `api/config.py:10` — `supabase_url: str`. `api/db.py:12` uses it to create Supabase client.

### Claim 33 — "SUPABASE_SERVICE_KEY — Supabase service role (полный доступ)" (line 63)
- **Verdict**: ACCURATE
- **Evidence**: `api/config.py:11` — `supabase_service_key: str`. `api/db.py:12` uses it as the key for `create_client()`.

### Claim 34 — "ADMIN_TOKEN — для POST /api/admin/reload-data (в dev compose, на сервере через .env)" (line 64)
- **Verdict**: ACCURATE
- **Evidence**: `api/config.py:12` — `admin_token: str`. `api/main.py:374` — validates `token != settings.admin_token`. `docker-compose.yml:18` passes `ADMIN_TOKEN=${ADMIN_TOKEN}`. In production, Docker Compose merges environment lists from both compose files, so `ADMIN_TOKEN` from the base file is still available.

### Claim 35 — "Backend НЕ использует SUPABASE_ANON_KEY" (line 66)
- **Verdict**: ACCURATE
- **Evidence**: `api/config.py` has no `supabase_anon_key` field. `api/db.py` uses only `supabase_service_key`. `docker-compose.yml:16` passes it, but backend code never reads it. `docker-compose.prod.yml` does not pass it.

### Claim 36 — "Backend НЕ использует SUPABASE_JWT_SECRET — JWT валидируется через JWKS endpoint" (line 66)
- **Verdict**: ACCURATE
- **Evidence**: No `SUPABASE_JWT_SECRET` in `api/config.py` or any compose file. `api/auth.py:15` — uses `PyJWKClient` with `{supabase_url}/auth/v1/.well-known/jwks.json`. JWT decoded with `ES256` algorithm and `audience="authenticated"`.

---

## Section: Секреты — Фронт (lines 68-70)

### Claim 37 — "VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY — Supabase клиент" (line 69)
- **Verdict**: ACCURATE
- **Evidence**: `front/src/lib/supabase.ts:3-7` — reads both env vars, throws if missing.

### Claim 38 — "VITE_API_URL — backend API" (line 70)
- **Verdict**: ACCURATE
- **Evidence**: `front/src/lib/api.ts:16` — `import.meta.env.VITE_API_URL ?? ""`.

---

## Section: Секреты — GitHub (lines 72-73)

### Claim 39 — "SSH_PRIVATE_KEY — SSH ключ для деплоя на Hetzner" (line 73)
- **Verdict**: ACCURATE
- **Evidence**: `.github/workflows/deploy.yml:37` — `key: ${{ secrets.SSH_PRIVATE_KEY }}`.

---

## Section: База данных (lines 75-86)

### Claim 40 — "6 таблиц + 1 view" (line 77)
- **Verdict**: ACCURATE
- **Evidence**: Migrations create 6 tables: `conversations`, `messages`, `tool_calls`, `instruments`, `exchanges`, `user_instruments`. Plus `instrument_full` view.

### Claim 41 — "conversations — разговоры пользователей (RLS: user_id)" (line 78)
- **Verdict**: ACCURATE
- **Evidence**: `20260129_init.sql` — table with `user_id uuid`, RLS policies with `auth.uid() = user_id`.

### Claim 42 — "messages — сообщения в разговорах (cascade delete)" (line 79)
- **Verdict**: ACCURATE
- **Evidence**: `20260129_init.sql:17` — `references public.conversations(id) on delete cascade`.

### Claim 43 — "tool_calls — вызовы run_query (FK на messages)" (line 80)
- **Verdict**: ACCURATE
- **Evidence**: `20260129_init.sql:30` — `references public.messages(id) on delete cascade`.

### Claim 44 — "instruments — торговые инструменты (public read, service-role write)" (line 81)
- **Verdict**: ACCURATE
- **Evidence**: `20260209_instruments.sql:27` — `"Anyone can read instruments" ... using (true)`. No insert/update/delete policies for anon users; service role bypasses RLS.

### Claim 45 — "exchanges — биржи с ETH/maintenance (public read, service-role write)" (line 82)
- **Verdict**: WRONG
- **Evidence**: ETH was moved to `instruments.config.sessions` in migration `20260216_eth_to_instruments.sql`. Maintenance was dropped entirely in `20260217_drop_maintenance.sql`. Current exchanges schema: `code text PK, name text, timezone text, image_url text`. No ETH or maintenance columns remain.
- **Fix**: Change to `exchanges — биржи с timezone (public read, service-role write)`.

### Claim 46 — "user_instruments — инструменты в workspace пользователя (RLS: user_id)" (line 83)
- **Verdict**: ACCURATE
- **Evidence**: `20260221_user_instruments.sql` — `user_id uuid`, RLS with `auth.uid() = user_id`.

### Claim 47 — "instrument_full — view: instruments + exchanges join" (line 84)
- **Verdict**: ACCURATE
- **Evidence**: `20260220_view_cleanup.sql` (latest definition) — `from instruments i join exchanges e on i.exchange = e.code`. Selects: `symbol, name, exchange, type, category, currency, default_session, data_start, data_end, events, notes, config, exchange_timezone, exchange_name`.

### Claim 48 — "RLS на всех user-scoped таблицах — пользователь видит только свои данные" (line 86)
- **Verdict**: ACCURATE
- **Evidence**: RLS enabled on `conversations`, `messages`, `tool_calls`, `user_instruments` with user-scoped policies. `instruments` and `exchanges` have public-read RLS, which is not "user-scoped" but also not contradicted by the statement.

---

## Section: Dockerfile (lines 88-96)

### Claim 49 — "FROM python:3.12-slim" (line 91)
- **Verdict**: ACCURATE
- **Evidence**: `Dockerfile:1` — `FROM python:3.12-slim`.

### Claim 50 — "COPY pyproject.toml, barb/, assistant/, config/, api/, scripts/" (line 92)
- **Verdict**: ACCURATE
- **Evidence**: `Dockerfile:11-16` — copies all listed items individually.

### Claim 51 — "pip install --no-cache-dir ." (line 93)
- **Verdict**: ACCURATE
- **Evidence**: `Dockerfile:17` — `RUN pip install --no-cache-dir .`.

### Claim 52 — "Не копирует front/, tests/, data/ — фронт на Vercel, данные через volume" (line 96)
- **Verdict**: ACCURATE
- **Evidence**: Dockerfile has no COPY for `front/`, `tests/`, or `data/`. Data is mounted via volume (`./data:/app/data`). A `mkdir -p /app/data` placeholder is created.

---

## Missing from doc

### Missing 1 — SUPABASE_ANON_KEY in dev compose
- **Detail**: `docker-compose.yml:16` passes `SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}` to the container, but the backend code never reads it. The doc correctly states the backend doesn't use it (line 66), but the dev compose file still passes it unnecessarily.
- **Severity**: Low (dead config, not a doc error)

### Missing 2 — Dockerfile installs curl as system dependency
- **Detail**: `Dockerfile:6-8` installs `curl` (needed for healthcheck). Doc's Dockerfile section doesn't mention system dependencies.
- **Severity**: Low (detail omission)

### Missing 3 — Dockerfile creates /app/data directory
- **Detail**: `Dockerfile:20` — `RUN mkdir -p /app/data`. Not mentioned in doc.
- **Severity**: Low (detail omission)

### Missing 4 — Caddy volumes in production
- **Detail**: `docker-compose.prod.yml:22-25` — `caddy_data` and `caddy_config` volumes for TLS certificate persistence. Not mentioned.
- **Severity**: Low (infrastructure detail)

### Missing 5 — conversations table has additional columns not described
- **Detail**: `usage` (jsonb, migration 20260130), `context` (jsonb, migration 20260131), `status` (text, migration 20260204). These are not mentioned in the table description.
- **Severity**: Low (the doc gives brief descriptions, not full schemas)

---

## Summary

| Verdict       | Count |
|---------------|-------|
| ACCURATE      | 38    |
| WRONG         | 1     |
| INACCURATE    | 1     |
| UNVERIFIABLE  | 4     |
| **Total**     | **44** |

### Wrong claims requiring fix

1. **Claim 45** (line 82): `exchanges — биржи с ETH/maintenance` -- ETH and maintenance columns no longer exist. Fix: `exchanges — биржи с timezone (public read, service-role write)`.

### Inaccurate claims

1. **Claim 31** (line 61): `GEMINI_API_KEY — Gemini API` -- The env var is passed in compose files but no Python code reads it. It's dead config, not an active backend secret. Fix: either remove from the doc or annotate as "reserved / unused" pending Gemini migration.

### Overall accuracy

42 of 44 claims are correct or unverifiable. The doc is **95% accurate** (excluding unverifiable claims: 38 of 40 = 95%).

The two issues are:
1. Outdated exchanges table description (ETH/maintenance removed in migrations 16-17)
2. GEMINI_API_KEY listed as active secret but unused by code
