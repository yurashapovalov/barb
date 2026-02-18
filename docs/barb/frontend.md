# Frontend Architecture

React SPA. Vite + TypeScript + React 19 + Tailwind v4 + shadcn/ui.

## Routes

```
/login              → LoginPage (Google OAuth + magic link)
/                   → HomePage (empty state — select a symbol)
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
│ NQ ←     │    candlestick chart   │  from query    │
│ ES       │    conversation list   │  result        │
│ CL       │    prompt input        │               │
│          │                        │               │
│ Chats    │  ChatPage:             │               │
│ chat 1   │    messages            │               │
│ chat 2   │    prompt input        │               │
│          │                        │               │
│ [+ Add]  │                        │               │
└──────────┴────────────────────────┴──────────────┘
```

Data panel appears on click of a data card in chat. Resizable via drag handle on desktop, full-screen on mobile.

## Component architecture

### Pattern: container / panel

Основной паттерн (не все страницы используют все три части):

- **Container** (`*-page.container.tsx`) — hooks, data loading, navigation, event handlers
- **Panel** (`*-panel.tsx`) — props-driven UI, may use React primitives (`useState`) and component-local hooks
- **Page** (`*-page.tsx`) — layout composition (ChatPage composes chat + data panels)

Исключение: `sidebar-panel.tsx` — потребляет 8 хуков напрямую (без контейнера), т.к. разделение создало бы 15+ prop interface.

```
hook → container → panel → component
```

### Provider tree

```
ErrorBoundary
  Toaster (sonner)
  BrowserRouter
    AuthProvider
      Routes
        /login                  ← вне AuthGuard
        AuthGuard
          RouteErrorBoundary
            InstrumentsProvider    ← user's instruments, loaded once
              ConversationsProvider  ← all conversations, loaded once
                SidebarProvider     ← open/close state
                  RootLayout        ← sidebar + main area
                    / /i/:symbol /i/:symbol/c/:id
        * → redirect to /       ← вне AuthGuard
```

### Providers

| Provider | Data | Pattern |
|----------|------|---------|
| AuthProvider | session, user | Supabase `onAuthStateChange` listener |
| InstrumentsProvider | user's instruments | fetch on mount, localStorage cache, error → toast |
| ConversationsProvider | all conversations | fetch on mount, localStorage cache, error → toast |
| SidebarProvider | open/close state | initialized from viewport width (1024px breakpoint), responds to resize |

InstrumentsProvider и ConversationsProvider expose `error` + `retry` for error recovery. All errors surface as sonner toasts.

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
    date.ts                              — relative date formatting (Today, Yesterday, Feb 10)
    format.ts                            — column label and number formatting
    parse-content.ts                     — parse message content → text + data block segments
    supabase.ts                          — Supabase client
    utils.ts                             — cn() for tailwind-merge

  hooks/
    use-auth.ts                          — AuthContext consumer
    use-chat.ts                          — messages, send, SSE callbacks, module-level cache
    use-conversations.ts                 — ConversationsContext consumer
    use-instruments.ts                   — InstrumentsContext consumer
    use-ohlc.ts                          — OHLC data fetch + localStorage cache
    use-panel-layout.ts                  — sidebar width (px) + data panel resize (% width)
    use-sidebar.ts                       — SidebarContext consumer
    use-theme.ts                         — dark/light/system, useSyncExternalStore

  components/
    auth/
      auth-provider.tsx                  — session state, Supabase listener, magic link
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
      sidebar-provider.tsx               — open/close state (viewport-based)
    panels/
      sidebar-panel.tsx                  — instruments list, chats list, user menu, theme
      instrument/
        instrument-panel.tsx             — candlestick chart, conversation list, prompt
        conversation-item.tsx            — conversation row with dropdown menu
      chat-panel.tsx                     — messages, prompt input, empty state
      data-panel.tsx                     — renders typed blocks (table, bar-chart, metrics-grid, area-chart, horizontal-bar)
      panel-header.tsx                   — shared header bar
      home-panel.tsx                     — home page content
      resize-handle.tsx                  — drag to resize data panel
    ai/
      conversation.tsx                   — scroll container, empty state, scroll button
      message.tsx                        — message bubble, generic action buttons
      prompt-input.tsx                   — textarea, submit button, provider
      data-card.tsx                      — inline data block in chat (clickable)
    charts/
      bar-chart.tsx                      — Recharts bar chart for grouped data
      candlestick-chart.tsx              — lightweight-charts OHLC + volume
    layout/
      root-layout.tsx                    — sidebar + main area (80vw sidebar on mobile)
    error-boundary.tsx                   — ErrorBoundary + RouteErrorBoundary
    ui/                                  — shadcn components (button, dialog, dropdown, etc.)

  pages/
    login/
      login-page.container.tsx           — redirect if already authenticated
      login-page.tsx                     — Google OAuth + magic link
    home/
      home-page.tsx                      — empty state (select a symbol)
    instrument/
      instrument-page.container.tsx      — loads conversations + OHLC for symbol
    chat/
      chat-page.container.tsx            — useChat, preview message, auto-send, sendRef
      chat-page.tsx                      — layout: chat panel + data panel + resize

  types/
    index.ts                             — Message, Conversation, Instrument, UserInstrument, DataBlock, Block (5 types), UsageBlock, ToolCall, SSE events

  __tests__/
    api.test.ts                          — API functions + SSE streaming
    date.test.ts                         — relative date formatting
    format.test.ts                       — column label + number formatting
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

Google OAuth + magic link (email OTP) via Supabase. Token в localStorage (Supabase default). Authenticated API calls send `Authorization: Bearer <token>`. Public endpoints (`listInstruments`, `getOHLC`) не требуют токена. Mid-session 401 triggers automatic sign-out via dynamic import of supabase client.

## Theme

`use-theme.ts` — `useSyncExternalStore` over localStorage. No provider needed. Applies `.dark` class to `<html>`. Sonner Toaster receives theme preference for matching.

## Deploy

Vercel. Auto-deploy from `main`. Root: `front/`. SPA rewrite via `vercel.json`.

Env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`.

## Key dependencies

- **lightweight-charts** — TradingView OSS candlestick chart (~45 KB)
- **recharts** — bar charts for grouped data, equity/drawdown area chart for backtests
- **streamdown** — streaming markdown renderer
- **use-stick-to-bottom** — auto-scroll in chat
- **@tanstack/react-table** — sortable data tables
