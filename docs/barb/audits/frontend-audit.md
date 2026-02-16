# Audit: frontend.md

**Date**: 2026-02-16
**Claims checked**: 75
**Correct**: 74 | **Wrong**: 1 | **Outdated**: 0 | **Unverifiable**: 0

## Issues

### [WRONG] Sidebar panel uses 8 hooks, not 7
- **Doc says**: "sidebar-panel.tsx — потребляет 7 хуков напрямую (без контейнера)"
- **Code says**: 8 hooks: `useState`, `useAuth`, `useTheme`, `useInstruments`, `useConversations`, `useParams`, `useNavigate`, `useSidebar`
- **File**: `front/src/components/panels/sidebar-panel.tsx:1-38`

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | React SPA, Vite + TypeScript + React 19 + Tailwind v4 + shadcn/ui | CORRECT | `front/package.json` — react ^19.2.0, tailwindcss ^4.1.18, vite ^7.2.4, shadcn ui/ components present |
| 2 | `/login` → LoginPage (Google OAuth + magic link) | CORRECT | `front/src/app.tsx:25`, `front/src/pages/login/login-page.tsx` — Google OAuth + email OTP |
| 3 | `/` → HomePage (empty state — select a symbol) | CORRECT | `front/src/app.tsx:32`, `front/src/components/panels/home-panel.tsx:12` — "Select a symbol to get started" |
| 4 | `/i/:symbol` → InstrumentPage (dashboard + conversation list) | CORRECT | `front/src/app.tsx:34`, `front/src/pages/instrument/instrument-page.container.tsx` |
| 5 | `/i/:symbol/c/:id` → ChatPage (chat + data panel) | CORRECT | `front/src/app.tsx:35`, `front/src/pages/chat/chat-page.tsx` — composes ChatPanel + DataPanel |
| 6 | `/i/:symbol/c/new` → ChatPage (auto-send initial message) | CORRECT | `front/src/pages/chat/chat-page.container.tsx:33,74-80` — id="new" triggers auto-send from sessionStorage |
| 7 | All routes except `/login` behind AuthGuard | CORRECT | `front/src/app.tsx:26` — `<Route element={<AuthGuard />}>` wraps all non-login routes |
| 8 | AuthGuard redirects to /login if no session, spinner while checking | CORRECT | `front/src/components/auth/auth-guard.tsx:8-16` — LoaderIcon spinner, Navigate to /login |
| 9 | Data panel appears on click of data card in chat | CORRECT | `front/src/pages/chat/chat-page.container.tsx:85-87` — handleSelectData toggles selectedData |
| 10 | Data panel resizable via drag handle on desktop | CORRECT | `front/src/pages/chat/chat-page.tsx:38` — ResizeHandle visible on lg+ |
| 11 | Data panel full-screen on mobile | CORRECT | `front/src/pages/chat/chat-page.tsx:40` — `fixed inset-0 z-50 lg:relative` |
| 12 | Container pattern: `*-page.container.tsx` — hooks, data loading, navigation | CORRECT | `login-page.container.tsx`, `instrument-page.container.tsx`, `chat-page.container.tsx` all follow this pattern |
| 13 | Panel pattern: `*-panel.tsx` — props-driven UI | CORRECT | `chat-panel.tsx`, `instrument-panel.tsx`, `data-panel.tsx`, `home-panel.tsx` all receive props |
| 14 | Page pattern: `*-page.tsx` — layout composition | CORRECT | `chat-page.tsx` composes ChatPanel + DataPanel + ResizeHandle |
| 15 | sidebar-panel.tsx uses 7 hooks directly (no container) | WRONG | `front/src/components/panels/sidebar-panel.tsx:31-38` — uses 8 hooks: useState, useAuth, useTheme, useInstruments, useConversations, useParams, useNavigate, useSidebar |
| 16 | Provider tree: ErrorBoundary → Toaster → BrowserRouter → AuthProvider | CORRECT | `front/src/app.tsx:20-23` |
| 17 | Provider tree: /login outside AuthGuard | CORRECT | `front/src/app.tsx:25` — before `<Route element={<AuthGuard />}>` |
| 18 | Provider tree: AuthGuard → RouteErrorBoundary → InstrumentsProvider → ConversationsProvider → SidebarProvider → RootLayout | CORRECT | `front/src/app.tsx:26-31` — exact nesting order matches |
| 19 | Provider tree: `*` → redirect to `/` outside AuthGuard | CORRECT | `front/src/app.tsx:43` — `<Route path="*" element={<Navigate to="/" replace />} />` |
| 20 | AuthProvider: session, user, Supabase onAuthStateChange listener | CORRECT | `front/src/components/auth/auth-provider.tsx:18-43` |
| 21 | InstrumentsProvider: user's instruments, fetch on mount, localStorage cache, error → toast | CORRECT | `front/src/components/instruments/instruments-provider.tsx:27-49` |
| 22 | ConversationsProvider: all conversations, fetch on mount, localStorage cache, error → toast | CORRECT | `front/src/components/conversations/conversations-provider.tsx:27-49` |
| 23 | SidebarProvider: open/close state, initialized from viewport width (1024px breakpoint) | CORRECT | `front/src/components/sidebar/sidebar-provider.tsx:5-8` — `LG_BREAKPOINT = 1024` |
| 24 | SidebarProvider responds to resize | CORRECT | `front/src/components/sidebar/sidebar-provider.tsx:10-14` — matchMedia change listener |
| 25 | InstrumentsProvider and ConversationsProvider expose error + retry | CORRECT | `instruments-context.ts:6-10`, `conversations-context.ts:7-9` — both have error + retry |
| 26 | All errors surface as sonner toasts | CORRECT | Both providers use `toast.error()` in catch blocks |
| 27 | ConversationsProvider loads ALL conversations, filtering at consumer | CORRECT | `conversations-provider.tsx:31` — `listConversations(token)` with no filter; `instrument-page.container.tsx:15` — filters by symbol |
| 28 | Cache: localStorage with readCache/writeCache in lib/cache.ts | CORRECT | `front/src/lib/cache.ts:3-18` |
| 29 | Cache: conversations and instruments use localStorage | CORRECT | Both providers use `readCache`/`writeCache` with per-user keys |
| 30 | Cache: module-level Map messageCache in use-chat.ts | CORRECT | `front/src/hooks/use-chat.ts:17` — `const messageCache = new Map<string, Message[]>()` |
| 31 | Cache: LRU eviction at 10 entries | CORRECT | `front/src/hooks/use-chat.ts:18,23` — `MAX_CACHE = 10`, deletes oldest |
| 32 | File: app.tsx — routes, Toaster, theme | CORRECT | `front/src/app.tsx` — BrowserRouter + Routes + Toaster + useTheme |
| 33 | File: main.tsx — entry point | CORRECT | `front/src/main.tsx` — createRoot, renders App |
| 34 | File: lib/api.ts — all API calls, SSE streaming, 401 handling | CORRECT | `front/src/lib/api.ts` — all API functions, sendMessageStream, checkAuth |
| 35 | File: lib/cache.ts — localStorage cache (readCache/writeCache) | CORRECT | `front/src/lib/cache.ts` |
| 36 | File: lib/format.ts — column label and number formatting | CORRECT | `front/src/lib/format.ts` — formatColumnLabel, formatValue |
| 37 | File: lib/parse-content.ts — parse message content → text + data block segments | CORRECT | `front/src/lib/parse-content.ts` — ContentSegment type, parseContent function |
| 38 | File: lib/supabase.ts — Supabase client | CORRECT | `front/src/lib/supabase.ts` — createClient |
| 39 | File: lib/utils.ts — cn() for tailwind-merge | CORRECT | `front/src/lib/utils.ts` — twMerge(clsx(inputs)) |
| 40 | File: hooks — all 8 hooks listed match actual files | CORRECT | Glob confirms all 8 hooks exist with matching names |
| 41 | File: components/auth — auth-provider.tsx, auth-guard.tsx | CORRECT | Both files exist and match descriptions |
| 42 | File: components/conversations — context + provider | CORRECT | `conversations-context.ts`, `conversations-provider.tsx` exist |
| 43 | File: components/instruments — context + provider + modal | CORRECT | `instruments-context.ts`, `instruments-provider.tsx`, `add-instrument-modal.tsx` exist |
| 44 | File: components/sidebar — context + provider | CORRECT | `sidebar-context.ts`, `sidebar-provider.tsx` exist |
| 45 | File: components/panels — all 7 panel files listed | CORRECT | All exist: sidebar-panel, instrument-panel, chat-panel, data-panel, panel-header, home-panel, resize-handle |
| 46 | File: components/ai — conversation, message, prompt-input, data-card | CORRECT | All 4 files exist |
| 47 | File: components/charts — bar-chart, candlestick-chart | CORRECT | Both files exist |
| 48 | File: components/layout — root-layout.tsx | CORRECT | File exists |
| 49 | File: components/error-boundary.tsx — ErrorBoundary + RouteErrorBoundary | CORRECT | `front/src/components/error-boundary.tsx` — both exported |
| 50 | File: components/ui/ — shadcn components | CORRECT | 11 UI component files exist |
| 51 | File: pages structure matches doc | CORRECT | login (container + page), home (page), instrument (container), chat (container + page) |
| 52 | File: types/index.ts — Message, Conversation, Instrument, UserInstrument, DataBlock, UsageBlock, ToolCall, SSE events | CORRECT | `front/src/types/index.ts` — all types present |
| 53 | File: __tests__ — 4 test files listed | CORRECT | api.test.ts, parse-content.test.ts, use-chat.test.ts, use-theme.test.ts |
| 54 | SSE: sendMessageStream parses events from POST /api/chat/stream | CORRECT | `front/src/lib/api.ts:215` |
| 55 | SSE event: text_delta — append to assistant message (streaming text) | CORRECT | `front/src/hooks/use-chat.ts:155-161` |
| 56 | SSE event: tool_start — add loading data card (shows spinner in chat) | CORRECT | `front/src/hooks/use-chat.ts:163-184` — adds loading block with status "loading" |
| 57 | SSE event: tool_end — update data card if error | CORRECT | `front/src/hooks/use-chat.ts:185-197` — updates to error status if event.error |
| 58 | SSE event: data_block — replace loading with result | CORRECT | `front/src/hooks/use-chat.ts:199-214` — replaces loading block |
| 59 | SSE event: done — finalize message, cache | CORRECT | `front/src/hooks/use-chat.ts:216-233` — updates content + usage, cacheSet |
| 60 | SSE event: persist — update message ID | CORRECT | `front/src/hooks/use-chat.ts:235-242` |
| 61 | SSE event: title_update — update conversation title | CORRECT | `front/src/hooks/use-chat.ts:244-246` |
| 62 | SSE event: error — set error, show toast | CORRECT | `front/src/hooks/use-chat.ts:247-250` |
| 63 | Type guards validate SSE events, no `as unknown as` casts | CORRECT | `front/src/lib/api.ts:159-193` — type guard functions, no casts in switch block |
| 64 | Error: Provider load failure → toast + error state for retry | CORRECT | Both providers catch errors, toast.error, set error state, expose retry |
| 65 | Error: Chat send failure → toast, optimistic messages rolled back | CORRECT | `front/src/hooks/use-chat.ts:252-258` — toast.error + filter out userMsg + assistantId |
| 66 | Error: SSE error event → toast from onError callback | CORRECT | `front/src/hooks/use-chat.ts:247-250` |
| 67 | Error: 401 → checkAuth in api.ts → sign out → redirect to login | CORRECT | `front/src/lib/api.ts:25-31` — dynamic import + signOut |
| 68 | Error: Remove chat failure → toast in catch block | CORRECT | `front/src/pages/chat/chat-page.container.tsx:116-118` |
| 69 | Error: Render crash → ErrorBoundary / RouteErrorBoundary (resets on navigation) | CORRECT | `front/src/components/error-boundary.tsx:47-49` — RouteErrorBoundary uses pathname as resetKey |
| 70 | Auth: Google OAuth + magic link via Supabase | CORRECT | `front/src/components/auth/auth-provider.tsx:45-57` |
| 71 | Auth: Token in localStorage (Supabase default) | CORRECT | Supabase JS default behavior, no custom storage config |
| 72 | Auth: Public endpoints (listInstruments, getOHLC) don't require token | CORRECT | `front/src/lib/api.ts:99-123` — no authHeaders on these calls |
| 73 | Theme: useSyncExternalStore over localStorage, no provider, .dark class on html | CORRECT | `front/src/hooks/use-theme.ts:1,16,48` |
| 74 | Deploy: Vercel, auto-deploy from main, root front/, SPA rewrite via vercel.json | CORRECT | `front/vercel.json` has SPA rewrite rule |
| 75 | Key deps: lightweight-charts, recharts, streamdown, use-stick-to-bottom, @tanstack/react-table | CORRECT | `front/package.json` — all 5 listed in dependencies |
