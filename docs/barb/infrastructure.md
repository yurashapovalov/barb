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
- Uvicorn, 2 воркера
- Данные (Parquet) в volume `/app/data`
- Деплой: SSH → git pull → docker compose up --build

### Фронт (Vercel)

- Root directory: `front/`
- Build: `npm run build` → `dist/`
- SPA rewrite: `vercel.json` → все пути на `index.html`

## DNS

- `getbarb.trade` → Vercel (фронт)
- `api.getbarb.trade` → 37.27.204.135 (Hetzner, бэкенд)

## CI (GitHub Actions)

Файл: `.github/workflows/deploy.yml`

1. **test** — `pip install -e .[dev]` → `ruff check .` → `pytest`
2. **deploy** — SSH на Hetzner → git pull → docker compose up

Deploy запускается только после успешных тестов.

## Окружения

### Production
- CORS: `https://getbarb.trade`
- ENV: `production`
- Логи: JSON формат
- 2 uvicorn воркера

### Development
- CORS: `*`
- ENV: `development`
- Логи: plaintext
- Hot-reload через volume mounts
- Все исходники монтируются в контейнер

## Секреты

- `ANTHROPIC_API_KEY` — Anthropic Claude API
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` — Supabase
- `SUPABASE_JWT_SECRET` — валидация JWT на бэкенде
- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL` — фронт (публичные)
- `SSH_PRIVATE_KEY` — GitHub Actions → Hetzner (в GitHub Secrets)

## База данных (Supabase)

Три таблицы: conversations, messages, tool_calls. RLS — пользователь видит только свои данные.
