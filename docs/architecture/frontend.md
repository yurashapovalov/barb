# Frontend (front/)

React SPA. Vite + TypeScript + Tailwind v4 + shadcn/ui.

## Стек

- **Vite** — сборка, dev server, HMR
- **React 19** + TypeScript
- **Tailwind CSS v4** — стили
- **shadcn/ui** — UI компоненты
- **React Router** — маршрутизация
- **Supabase JS** — авторизация
- **Plain fetch** — запросы к API (SSE streaming)

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

## Структура

```
front/src/
  app.tsx                   — маршрутизация
  main.tsx                  — точка входа
  lib/
    supabase.ts             — Supabase клиент
    api.ts                  — SSE streaming (sendMessageStream)
    utils.ts                — cn() для shadcn
  hooks/
    use-auth.ts             — доступ к AuthContext
    use-chat.ts             — управление сообщениями, SSE handlers
    use-conversations.ts    — CRUD разговоров
  types/
    index.ts                — Message, Conversation, DataBlock, UsageBlock, ToolCall, SSE events
  components/
    ui/                     — shadcn компоненты
    auth/                   — AuthProvider, AuthGuard, LoginPage
    ai/                     — ChatMessage, DataCard, MarkdownContent
    sidebar/                — ConversationList, ConversationItem
    layout/                 — RootLayout
  pages/
    chat/                   — ChatPage container и presenter
```

## SSE Handling

`use-chat.ts` обрабатывает SSE events от API:
- `onTextDelta` — добавляет текст к ответу
- `onToolStart` — показывает loading state на data card
- `onToolEnd` — показывает error если был
- `onDataBlock` — заменяет loading на данные
- `onDone` — финализирует сообщение
- `onPersist` — обновляет message ID
- `onTitleUpdate` — обновляет title в sidebar

## Деплой

Vercel. Автодеплой из main. Root directory: `front/`. Env vars: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL.
