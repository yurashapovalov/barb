# Инфраструктура

## Деплой

```
GitHub (yurashapovalov/barb)
    ↓ push в main
    ├── GitHub Actions → тесты + деплой бэкенда на Hetzner
    └── Vercel → автодеплой фронта
```

### Бэкенд (Hetzner, 37.27.204.135)

- Docker Compose: `docker-compose.yml` + `docker-compose.prod.yml`
- Caddy reverse proxy: автоматический TLS, `api.getbarb.trade` → `api:8000`
- Uvicorn, 2 воркера
- Данные (Parquet) в volume `./data:/app/data`
- Деплой: SSH → `cd /opt/barb` → `git pull` → `docker compose up -d --build` → `docker system prune -f`

### Фронт (Vercel)

- Root directory: `front/`
- Build: `tsc -b && vite build` → `dist/`
- SPA rewrite: `vercel.json` → все пути на `index.html`

## DNS

- `getbarb.trade` → Vercel (фронт)
- `api.getbarb.trade` → 37.27.204.135 (Caddy → Uvicorn)

## CI (GitHub Actions)

Файл: `.github/workflows/deploy.yml`

1. **test** — `pip install -e .[dev]` → `ruff check .` → `pytest --tb=short -q`
2. **deploy** — SSH на Hetzner → git pull → docker compose up

Deploy запускается только после успешных тестов (`needs: test`).

## Окружения

### Production (`docker-compose.prod.yml`)
- CORS: `https://getbarb.trade,http://localhost:3000`
- ENV: `production`
- Логи: JSON формат (`_JSONFormatter`)
- 2 uvicorn воркера (`--workers 2`)
- Caddy: порты 80/443, автоматический TLS

### Development (`docker-compose.yml`)
- CORS: `*` (default)
- ENV: `development`
- Логи: plaintext
- Hot-reload (`--reload`) через volume mounts
- Исходники монтируются: `barb/`, `assistant/`, `api/`, `config/`, `data/`
- Healthcheck: `curl -f http://localhost:8000/health` каждые 30s

## Секреты

### Бэкенд (env vars)
- `ANTHROPIC_API_KEY` — Claude API
- `SUPABASE_URL` — Supabase endpoint
- `SUPABASE_SERVICE_KEY` — Supabase service role (полный доступ)
- `ADMIN_TOKEN` — для `POST /api/admin/reload-data` (в dev compose, на сервере через `.env`)

Backend НЕ использует `SUPABASE_ANON_KEY` и `SUPABASE_JWT_SECRET` — JWT валидируется через JWKS endpoint.

### Фронт (публичные)
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` — Supabase клиент
- `VITE_API_URL` — backend API

### GitHub Secrets
- `SSH_PRIVATE_KEY` — SSH ключ для деплоя на Hetzner

## База данных (Supabase)

6 таблиц + 1 view:
- `conversations` — разговоры пользователей (RLS: `user_id`)
- `messages` — сообщения в разговорах (cascade delete)
- `tool_calls` — вызовы run_query (FK на messages)
- `instruments` — торговые инструменты (public read, service-role write)
- `exchanges` — биржи с timezone (public read, service-role write)
- `user_instruments` — инструменты в workspace пользователя (RLS: `user_id`)
- `instrument_full` — view: instruments + exchanges join

RLS на всех user-scoped таблицах — пользователь видит только свои данные.

## Dockerfile

```
FROM python:3.12-slim
COPY pyproject.toml, barb/, assistant/, config/, api/, scripts/
pip install --no-cache-dir .
```

Не копирует `front/`, `tests/`, `data/` — фронт на Vercel, данные через volume.
