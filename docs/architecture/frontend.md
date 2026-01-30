# Frontend (front/)

React SPA. Vite + TypeScript + Tailwind v4 + shadcn/ui.

## Стек

- **Vite** — сборка, dev server, HMR
- **React 19** + TypeScript
- **Tailwind CSS v4** — стили
- **shadcn/ui** — UI компоненты
- **React Router** — маршрутизация
- **Supabase JS** — авторизация + хранение чатов
- **Plain fetch** — запросы к API

## Маршруты

- `/login` — страница логина (Google OAuth)
- `/` — новый чат
- `/c/:id` — существующий чат

Все маршруты кроме `/login` защищены AuthGuard — редирект на `/login` если нет сессии.

## Авторизация

Google OAuth через Supabase. Поток:
1. Пользователь нажимает "Sign in with Google"
2. Редирект на Google → согласие → редирект на Supabase callback
3. Supabase создаёт сессию + JWT
4. Фронт сохраняет сессию, шлёт JWT в API

AuthProvider — единственный глобальный стейт (контекст). Предоставляет: user, session, loading, signInWithGoogle, signOut.

## Хранение данных

Фронт напрямую работает с Supabase (не через API):
- Создание/загрузка чатов (conversations)
- Сохранение/загрузка сообщений (messages)

API не трогает Supabase. API только обрабатывает чат-запросы и возвращает ответ.

## Структура

```
front/src/
  app.tsx                   — маршрутизация
  main.tsx                  — точка входа
  lib/
    supabase.ts             — Supabase клиент
    api.ts                  — sendMessage() → POST /api/chat
    utils.ts                — cn() для shadcn
  hooks/
    use-auth.ts             — доступ к AuthContext
    use-chat.ts             — управление одним чатом (TODO)
    use-conversations.ts    — список чатов (TODO)
  types/
    index.ts                — Message, Conversation, DataBlock, UsageBlock, ToolCall
  components/
    ui/                     — shadcn компоненты
    auth/                   — AuthProvider, AuthGuard, LoginPage
    chat/                   — ChatPage (TODO)
    sidebar/                — список чатов (TODO)
    layout/                 — RootLayout
```

## Деплой

Vercel. Автодеплой из main. Root directory: `front/`. Env vars: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL.
