# Audit: infrastructure.md

**Date**: 2026-02-16
**Claims checked**: 42
**Correct**: 39 | **Wrong**: 1 | **Outdated**: 0 | **Unverifiable**: 2

## Issues

### [WRONG] Deploy command simplified — missing compose file flags
- **Doc says**: `docker compose up -d --build` (line 18)
- **Code says**: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
- **File**: `.github/workflows/deploy.yml:41`

The deploy script uses both compose files explicitly with `-f` flags. The doc omits this, which matters because the prod override is what enables Caddy, 2 workers, and production env vars. Someone copying the doc command would deploy without prod overrides.

### [UNVERIFIABLE] DNS records
- **Doc says**: `getbarb.trade` → Vercel, `api.getbarb.trade` → 37.27.204.135
- **Why**: DNS configuration is external — cannot verify from code. The Caddyfile references `api.getbarb.trade` (consistent), and Vercel config exists in `front/vercel.json` (consistent), but actual DNS records cannot be confirmed from the repo.

### [UNVERIFIABLE] GitHub repo name
- **Doc says**: `yurashapovalov/barb`
- **Why**: Cannot verify the remote repo name from local code alone. The deploy.yml uses `git pull origin main` but does not reference the repo URL.

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | GitHub Actions triggers on push to main | CORRECT | `.github/workflows/deploy.yml:4-5` — `on: push: branches: [main]` |
| 2 | GitHub Actions runs tests + deploy | CORRECT | `.github/workflows/deploy.yml:8,28` — `test` and `deploy` jobs |
| 3 | Vercel autodeploys frontend | CORRECT | `front/vercel.json` exists with SPA rewrite config |
| 4 | Backend on Hetzner, IP 37.27.204.135 | CORRECT | `.github/workflows/deploy.yml:35` — `host: 37.27.204.135` |
| 5 | Docker Compose uses `docker-compose.yml` + `docker-compose.prod.yml` | CORRECT | Both files exist; `.github/workflows/deploy.yml:41` uses both with `-f` |
| 6 | Caddy reverse proxy: `api.getbarb.trade` → `api:8000` | CORRECT | `Caddyfile:1-3` — `api.getbarb.trade { reverse_proxy api:8000 }` |
| 7 | Caddy provides automatic TLS | CORRECT | `Caddyfile` uses domain name (Caddy auto-TLS), `docker-compose.prod.yml:19` exposes ports 80/443 |
| 8 | Uvicorn, 2 workers | CORRECT | `docker-compose.prod.yml:11` — `--workers 2` |
| 9 | Data in volume `./data:/app/data` | CORRECT | `docker-compose.yml:7` — `./data:/app/data` |
| 10 | Deploy: SSH → cd /opt/barb → git pull → docker compose up -d --build → docker system prune -f | WRONG | `.github/workflows/deploy.yml:38-42` — actual command is `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`, not plain `docker compose up -d --build` |
| 11 | Frontend root directory: `front/` | CORRECT | `front/package.json` exists, `front/vercel.json` exists |
| 12 | Frontend build: `tsc -b && vite build` → `dist/` | CORRECT | `front/package.json:8` — `"build": "tsc -b && vite build"` (Vite defaults to `dist/`) |
| 13 | SPA rewrite: vercel.json routes all paths to index.html | CORRECT | `front/vercel.json:3` — `{ "source": "/(.*)", "destination": "/index.html" }` |
| 14 | CI file: `.github/workflows/deploy.yml` | CORRECT | File exists at that path |
| 15 | CI test step: `pip install -e .[dev]` → `ruff check .` → `pytest --tb=short -q` | CORRECT | `.github/workflows/deploy.yml:20,23,26` — exact commands match |
| 16 | CI deploy: SSH to Hetzner → git pull → docker compose up | CORRECT | `.github/workflows/deploy.yml:32-42` |
| 17 | Deploy needs: test (runs only after successful tests) | CORRECT | `.github/workflows/deploy.yml:29` — `needs: test` |
| 18 | Prod CORS: `https://getbarb.trade,http://localhost:3000` | CORRECT | `docker-compose.prod.yml:7` — `CORS_ORIGINS=${CORS_ORIGINS:-https://getbarb.trade,http://localhost:3000}` |
| 19 | Prod ENV: `production` | CORRECT | `docker-compose.prod.yml:6` — `ENV=production` |
| 20 | Prod logs: JSON format (`_JSONFormatter`) | CORRECT | `api/main.py:30-46` — `if os.getenv("ENV") == "production":` uses `_JSONFormatter` |
| 21 | Prod: 2 uvicorn workers (`--workers 2`) | CORRECT | `docker-compose.prod.yml:11` — `--workers 2` |
| 22 | Caddy: ports 80/443 | CORRECT | `docker-compose.prod.yml:19-20` — `"80:80"` and `"443:443"` |
| 23 | Dev CORS: `*` (default) | CORRECT | `api/main.py:76` — `os.getenv("CORS_ORIGINS", "*").split(",")`, dev compose doesn't set CORS_ORIGINS |
| 24 | Dev ENV: `development` | CORRECT | `docker-compose.yml:17` — `ENV=development` |
| 25 | Dev logs: plaintext | CORRECT | `api/main.py:48-52` — else branch uses `logging.basicConfig` with text format |
| 26 | Dev hot-reload (`--reload`) via volume mounts | CORRECT | `docker-compose.yml:18` — `--reload`, lines 7-11 mount source dirs |
| 27 | Dev source mounts: `barb/`, `assistant/`, `api/`, `config/`, `data/` | CORRECT | `docker-compose.yml:7-11` — all five directories mounted |
| 28 | Dev healthcheck: `curl -f http://localhost:8000/health` every 30s | CORRECT | `docker-compose.yml:20-23` — exact command and `interval: 30s` |
| 29 | Secret: `ANTHROPIC_API_KEY` | CORRECT | `docker-compose.yml:13`, `api/config.py:9` |
| 30 | Secret: `SUPABASE_URL` | CORRECT | `docker-compose.yml:14`, `api/config.py:10` |
| 31 | Secret: `SUPABASE_SERVICE_KEY` | CORRECT | `docker-compose.yml:15`, `api/config.py:11` |
| 32 | Secret: `ADMIN_TOKEN` for `POST /api/admin/reload-data` (in dev compose, server via .env) | CORRECT | `docker-compose.yml:16` — `ADMIN_TOKEN=${ADMIN_TOKEN}`, `api/main.py:370-374` — endpoint exists |
| 33 | Backend does NOT use `SUPABASE_ANON_KEY` or `SUPABASE_JWT_SECRET` | CORRECT | No Python file imports or references these; `api/config.py` only has 4 settings; `api/auth.py` uses JWKS |
| 34 | JWT validated via JWKS endpoint | CORRECT | `api/auth.py:15-16` — `PyJWKClient(url)` with `.well-known/jwks.json` |
| 35 | Frontend env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL` | CORRECT | `front/src/lib/supabase.ts:3,6` and `front/src/lib/api.ts:16` |
| 36 | GitHub secret: `SSH_PRIVATE_KEY` | CORRECT | `.github/workflows/deploy.yml:37` — `key: ${{ secrets.SSH_PRIVATE_KEY }}` |
| 37 | 6 tables + 1 view | CORRECT | conversations, messages, tool_calls, instruments, exchanges, user_instruments + instrument_full view |
| 38 | Table descriptions (conversations with RLS user_id, messages cascade, tool_calls FK, instruments public read, exchanges public read, user_instruments RLS, instrument_full as join view) | CORRECT | Verified across all migration files |
| 39 | RLS on all user-scoped tables | CORRECT | `20260129_init.sql:44-46` enables RLS on conversations/messages/tool_calls; `20260221_user_instruments.sql:14` enables RLS on user_instruments |
| 40 | Dockerfile: FROM python:3.12-slim | CORRECT | `Dockerfile:1` |
| 41 | Dockerfile copies: pyproject.toml, barb/, assistant/, config/, api/, scripts/ | CORRECT | `Dockerfile:11-16` — all six items copied |
| 42 | Dockerfile does NOT copy front/, tests/, data/ | CORRECT | `Dockerfile` — none of these appear in COPY commands; data created via `mkdir -p /app/data` |
