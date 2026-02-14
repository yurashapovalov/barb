# Frontend Architecture

React SPA. Vite + TypeScript + React 19 + Tailwind v4 + shadcn/ui.

## Routes

```
/login              → LoginPage (Google OAuth)
/                   → HomePage (redirect to last instrument or empty state)
/i/:symbol          → InstrumentPage (dashboard + conversation list)
/i/:symbol/c/:id    → ChatPage (chat + data panel)
/i/:symbol/c/new    → ChatPage (auto-send initial message)
```

All routes except `/login` are behind `AuthGuard` — redirects to `/login` if no session, shows spinner while checking.

## Layout

```
┌──────────┬────────────────────────┬──────────────┐
│ sidebar  │      main area         │  data panel   │
│          │                        │  (optional)   │
│ [user]   │  InstrumentPage:       │               │
│          │    instrument header   │  table/chart   │
│ NQ ←     │    conversation list   │  from query    │
│ ES       │    prompt input        │  result        │
│ CL       │                        │               │
│          │  ChatPage:             │               │
│ Chats    │    messages            │               │
│ chat 1   │    prompt input        │               │
│ chat 2   │                        │               │
│          │                        │               │
│ [+ Add]  │                        │               │
└──────────┴────────────────────────┴──────────────┘
```

Data panel appears on click of a data card in chat. Resizable via drag handle on desktop, full-screen overlay on mobile.

## Component architecture

### Pattern: container / panel

Every page follows the same split:

- **Container** (`*-page.container.tsx`) — hooks, data loading, navigation, event handlers
- **Panel** (`*-panel.tsx`) — pure props, renders UI
- **Page** (`*-page.tsx`) — layout composition (optional, ChatPage composes chat + data panels)

```
hook → container → panel → component
```

Panels never import hooks directly. Exception: `sidebar-panel.tsx` (documented — splitting would create 15+ prop interface).

### Provider tree

```
ErrorBoundary
  Toaster (sonner)
  BrowserRouter
    AuthProvider
      AuthGuard
        RouteErrorBoundary
          InstrumentsProvider    ← user's instruments, loaded once
            ConversationsProvider  ← all conversations, loaded once
              SidebarProvider     ← open/close state
                RootLayout        ← sidebar + main area
                  Routes
```

### Providers

| Provider | Data | Pattern |
|----------|------|---------|
| AuthProvider | session, user | Supabase `onAuthStateChange` listener |
| InstrumentsProvider | user's instruments | fetch on mount, localStorage cache, error → toast |
| ConversationsProvider | all conversations | fetch on mount, localStorage cache, error → toast |
| SidebarProvider | open/close state | localStorage persisted |

Providers expose `error` + `retry` for error recovery. All errors surface as sonner toasts.

ConversationsProvider loads ALL conversations. Filtering by instrument happens at the consumer (instrument-page.container filters by `:symbol`).

### Cache

Two layers:
- **localStorage** (`readCache`/`writeCache` in `lib/cache.ts`) — conversations, instruments. Shown immediately on mount, replaced by fresh API data.
- **Module-level Map** (`messageCache` in `use-chat.ts`) — chat messages. Survives unmount/remount, LRU eviction at 10 entries.

## File structure

```
front/src/
  app.tsx                                — routes, Toaster, theme
  main.tsx                               — entry point

  lib/
    api.ts                               — all API calls, SSE streaming, 401 handling
    cache.ts                             — localStorage cache (readCache/writeCache)
    format.ts                            — number/date formatting
    parse-content.ts                     — parse message content → text + data block segments
    supabase.ts                          — Supabase client
    utils.ts                             — cn() for tailwind-merge

  hooks/
    use-auth.ts                          — AuthContext consumer
    use-chat.ts                          — messages, send, SSE callbacks, module-level cache
    use-conversations.ts                 — ConversationsContext consumer
    use-instruments.ts                   — InstrumentsContext consumer
    use-panel-layout.ts                  — data panel resize (% width)
    use-sidebar.ts                       — SidebarContext consumer
    use-theme.ts                         — dark/light/system, useSyncExternalStore

  components/
    auth/
      auth-provider.tsx                  — session state, Supabase listener
      auth-guard.tsx                     — redirect if unauthenticated, spinner while loading
    conversations/
      conversations-context.ts           — context type
      conversations-provider.tsx         — fetch, cache, CRUD, error/retry
    instruments/
      instruments-context.ts             — context type
      instruments-provider.tsx           — fetch, cache, add/remove, error/retry
      add-instrument-modal.tsx           — search + add instrument dialog
    sidebar/
      sidebar-context.ts                 — context type
      sidebar-provider.tsx               — open/close state
    panels/
      sidebar-panel.tsx                  — instruments list, chats list, user menu, theme
      instrument-panel.tsx               — instrument header, conversation list, prompt
      chat-panel.tsx                     — messages, prompt input, empty state
      data-panel.tsx                     — table + chart from query result
      panel-header.tsx                   — shared header bar
      home-panel.tsx                     — home page content
      resize-handle.tsx                  — drag to resize data panel
    ai/
      conversation.tsx                   — scroll container, empty state, scroll button
      message.tsx                        — message bubble, actions (like/dislike)
      prompt-input.tsx                   — textarea, submit button, provider
      data-card.tsx                      — inline data block in chat (clickable)
    charts/
      bar-chart.tsx                      — Recharts bar chart for data cards
    layout/
      root-layout.tsx                    — sidebar + main area + mobile overlay
    error-boundary.tsx                   — ErrorBoundary + RouteErrorBoundary
    ui/                                  — shadcn components (button, dialog, dropdown, etc.)

  pages/
    login/
      login-page.container.tsx           — redirect if already authenticated
      login-page.tsx                     — Google OAuth button
    home/
      home-page.tsx                      — redirect to first instrument or empty state
    instrument/
      instrument-page.container.tsx      — loads conversations for symbol, passes to panel
    chat/
      chat-page.container.tsx            — useChat, preview message, auto-send, sendRef
      chat-page.tsx                      — layout: chat panel + data panel + resize

  types/
    index.ts                             — Message, Conversation, Instrument, DataBlock, SSE events

  __tests__/
    api.test.ts                          — API functions + SSE streaming
    parse-content.test.ts                — content parsing
    use-chat.test.ts                     — chat hook lifecycle
    use-theme.test.ts                    — theme switching
```

## SSE streaming

`api.ts` → `sendMessageStream()` parses SSE events from `POST /api/chat/stream`:

| Event | Handler | Effect |
|-------|---------|--------|
| `text_delta` | append to assistant message | streaming text |
| `tool_start` | add loading data card | shows spinner in chat |
| `tool_end` | update data card if error | shows error on card |
| `data_block` | replace loading with result | table/chart appears |
| `done` | finalize message, cache | message complete |
| `persist` | update message ID | real ID from DB |
| `title_update` | update conversation title | sidebar reflects new title |
| `error` | set error, show toast | user sees error |

Type guards (`isToolStartEvent`, `isTextDeltaEvent`, etc.) validate each event — no `as unknown as` casts.

## Error handling

All errors surface as **sonner toasts** — one place, consistent.

| Source | How |
|--------|-----|
| Provider load failure | toast in catch block, error state for retry |
| Chat send failure | toast in useChat catch, optimistic messages rolled back |
| SSE error event | toast from onError callback |
| 401 response | `checkAuth()` in api.ts → sign out → redirect to login |
| Remove chat failure | toast in catch block |
| Render crash | ErrorBoundary / RouteErrorBoundary (resets on navigation) |

## Auth

Google OAuth via Supabase. Token in localStorage (Supabase default). All API calls send `Authorization: Bearer <token>`. Mid-session 401 triggers automatic sign-out via dynamic import of supabase client.

## Theme

`use-theme.ts` — `useSyncExternalStore` over localStorage. No provider needed. Applies `.dark` class to `<html>`. Sonner Toaster receives theme preference for matching.

## Deploy

Vercel. Auto-deploy from `main`. Root: `front/`. SPA rewrite via `vercel.json`.

Env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`.

## Next: Phase 3

### Candlestick chart on instrument dashboard

Library: TradingView Lightweight Charts (~45 KB gzipped).

- Candlestick + volume on `/i/:symbol`
- New endpoint: `GET /api/instruments/:symbol/ohlc?timeframe=1d&limit=500`
- New component: `components/charts/candlestick-chart.tsx`

### Data card charts

Library: Recharts (already installed, `bar-chart.tsx` exists).

Charts inside data cards (query results in chat):
- Bar chart: grouped categorical data (by weekday, by month)
- Line chart: time series trends
- Histogram: distributions
- Area chart: equity curves

### Other dashboard content

- Instrument info card (contract specs, sessions, holidays)
- Backtest results list
- Saved queries / bookmarks
