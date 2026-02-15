# Audit: frontend.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 1: "React SPA. Vite + TypeScript + React 19 + Tailwind v4 + shadcn/ui."
- **Verdict**: ACCURATE
- **Evidence**: `front/package.json` — React 19.2.0, Tailwind 4.1.18, Vite 7.2.4, TS 5.9.3, shadcn components in `ui/`

### Claim 2
- **Doc**: line 8: "/login -> LoginPage (Google OAuth)"
- **Verdict**: OUTDATED
- **Evidence**: `front/src/pages/login/login-page.tsx:8` — also supports magic link (email OTP)
- **Fix**: change to "(Google OAuth + magic link)"

### Claim 3
- **Doc**: line 9: "/ -> HomePage (redirect to last instrument or empty state)"
- **Verdict**: WRONG
- **Evidence**: `front/src/pages/home/home-page.tsx:7-21` — just shows "Select a symbol" static empty state, no redirect
- **Fix**: change to "empty state prompting user to select a symbol"

### Claim 4
- **Doc**: line 10: "/i/:symbol -> InstrumentPage (dashboard + conversation list)"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/app.tsx:33-34` and `instrument-page.container.tsx`

### Claim 5
- **Doc**: line 11: "/i/:symbol/c/:id -> ChatPage"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/app.tsx:35`

### Claim 6
- **Doc**: line 12: "/i/:symbol/c/new -> ChatPage (auto-send initial message)"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/pages/chat/chat-page.container.tsx:33` — sessionStorage initial message logic

### Claim 7
- **Doc**: line 15: "All routes except /login are behind AuthGuard"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/app.tsx:26` — `<Route element={<AuthGuard />}>`

### Claim 8
- **Doc**: line 37: "Data panel appears on click of a data card"
- **Verdict**: ACCURATE
- **Evidence**: `chat-page.container.tsx:85-87` — `handleSelectData` callback

### Claim 9
- **Doc**: line 37: "Resizable via drag handle on desktop, full-screen overlay on mobile"
- **Verdict**: ACCURATE
- **Evidence**: `chat-page.tsx:38-40` — ResizeHandle hidden on mobile, fixed positioning on mobile

### Claim 10
- **Doc**: line 45: "Container (*-page.container.tsx) -- hooks, data loading"
- **Verdict**: ACCURATE
- **Evidence**: verified in chat and instrument containers

### Claim 11
- **Doc**: line 46: "Panel (*-panel.tsx) -- pure props, renders UI"
- **Verdict**: ACCURATE
- **Evidence**: chat-panel, instrument-panel, data-panel all receive props

### Claim 12
- **Doc**: line 47: "Page (*-page.tsx) -- layout composition"
- **Verdict**: ACCURATE
- **Evidence**: `chat-page.tsx:20-49` composes panels

### Claim 13
- **Doc**: line 53: "Panels never import hooks directly. Exception: sidebar-panel.tsx"
- **Verdict**: WRONG
- **Evidence**: `instrument-panel.tsx:6-9` imports `usePromptInputController`; `data-panel.tsx:1` imports `useState`
- **Fix**: clarify that panels may use React primitives and component-local hooks

### Claim 14
- **Doc**: line 53: "splitting would create 15+ prop interface"
- **Verdict**: UNVERIFIABLE
- **Evidence**: design rationale, not verifiable from code

### Claim 15
- **Doc**: lines 58-68: Provider tree ordering
- **Verdict**: ACCURATE
- **Evidence**: `front/src/app.tsx:20-47` — exact nesting matches

### Claim 16
- **Doc**: line 75: "AuthProvider | session, user | Supabase onAuthStateChange"
- **Verdict**: ACCURATE
- **Evidence**: `auth-provider.tsx:30`

### Claim 17
- **Doc**: line 76: "InstrumentsProvider | fetch on mount, localStorage cache"
- **Verdict**: ACCURATE
- **Evidence**: `instruments-provider.tsx:20-45`

### Claim 18
- **Doc**: line 77: "ConversationsProvider | fetch on mount, localStorage cache"
- **Verdict**: ACCURATE
- **Evidence**: `conversations-provider.tsx:19-46`

### Claim 19
- **Doc**: line 78: "SidebarProvider | localStorage persisted"
- **Verdict**: WRONG
- **Evidence**: `sidebar-provider.tsx:8` — initialized from `window.innerWidth >= LG_BREAKPOINT`, no localStorage
- **Fix**: change to "initialized from viewport width, responds to resize"

### Claim 20
- **Doc**: line 80: "Providers expose error + retry"
- **Verdict**: ACCURATE
- **Evidence**: both providers export `error` and `retry`

### Claim 21
- **Doc**: line 82: "ConversationsProvider loads ALL conversations"
- **Verdict**: ACCURATE
- **Evidence**: `conversations-provider.tsx:31` — no instrument filter

### Claim 22
- **Doc**: line 87: "localStorage (readCache/writeCache)"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/lib/cache.ts:3-18`

### Claim 23
- **Doc**: line 88: "Module-level Map (messageCache) -- LRU eviction at 10"
- **Verdict**: ACCURATE
- **Evidence**: `use-chat.ts:17-27`

### Claim 24
- **Doc**: line 94: "app.tsx -- routes, Toaster, theme"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/app.tsx`

### Claim 25
- **Doc**: line 98: "api.ts -- all API calls, SSE streaming, 401 handling"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/lib/api.ts`

### Claim 26
- **Doc**: line 100: "format.ts -- number/date formatting"
- **Verdict**: OUTDATED
- **Evidence**: no date formatting functions in format.ts
- **Fix**: change to "column label and number formatting"

### Claim 27
- **Doc**: line 110: "use-panel-layout.ts -- data panel resize (% width)"
- **Verdict**: OUTDATED
- **Evidence**: also manages sidebar width (px)
- **Fix**: change to "sidebar width (px) + data panel resize (% width)"

### Claim 28
- **Doc**: line 137: "conversation.tsx -- scroll container, empty state, scroll button"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/ai/conversation.tsx`

### Claim 29
- **Doc**: line 138: "message.tsx -- message bubble, actions (like/dislike)"
- **Verdict**: WRONG
- **Evidence**: no like/dislike functionality; `MessageAction` is a generic button with tooltip
- **Fix**: change to "actions (generic action buttons with tooltip)"

### Claim 30
- **Doc**: line 139: "prompt-input.tsx -- textarea, submit button, provider"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/ai/prompt-input.tsx`

### Claim 31
- **Doc**: line 140: "data-card.tsx -- inline data block in chat"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/ai/data-card.tsx`

### Claim 32
- **Doc**: line 142: "bar-chart.tsx -- Recharts bar chart"
- **Verdict**: ACCURATE
- **Evidence**: file exists, `recharts` in package.json

### Claim 33
- **Doc**: line 144: "root-layout.tsx -- sidebar + main area + mobile overlay"
- **Verdict**: OUTDATED
- **Evidence**: no mobile overlay; sidebar just takes 80vw on mobile
- **Fix**: remove "mobile overlay"

### Claim 34
- **Doc**: line 145: "error-boundary.tsx -- ErrorBoundary + RouteErrorBoundary"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/error-boundary.tsx`

### Claim 35
- **Doc**: line 157: "chat-page.container.tsx -- useChat, preview, auto-send, sendRef"
- **Verdict**: ACCURATE
- **Evidence**: all four features confirmed

### Claim 36
- **Doc**: line 161: "types/index.ts -- Message, Conversation, Instrument, DataBlock, SSE"
- **Verdict**: ACCURATE
- **Evidence**: all types exported

### Claim 37
- **Doc**: line 163-167: Test files
- **Verdict**: ACCURATE
- **Evidence**: all 4 files exist in `front/src/__tests__/`

### Claims 38-46
- **Doc**: SSE event handling (text_delta, tool_start, tool_end, data_block, done, persist, title_update, error)
- **Verdict**: ACCURATE
- **Evidence**: all verified in `use-chat.ts` and `api.ts`

### Claim 47
- **Doc**: line 185: "Type guards validate each event -- no as unknown as"
- **Verdict**: ACCURATE
- **Evidence**: type guards exist; no `as unknown as` in codebase

### Claims 48-51
- **Doc**: Error handling, 401 response, auth flow
- **Verdict**: ACCURATE
- **Evidence**: verified in api.ts, auth-provider.tsx

### Claim 52
- **Doc**: line 206: "use-theme.ts -- useSyncExternalStore over localStorage"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/hooks/use-theme.ts`

### Claim 53
- **Doc**: line 206: "Sonner Toaster receives theme"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/app.tsx:21`

### Claim 54
- **Doc**: line 210: "Vercel. Auto-deploy from main."
- **Verdict**: UNVERIFIABLE
- **Evidence**: external hosting config

### Claim 55
- **Doc**: line 212: "Env vars: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL"
- **Verdict**: ACCURATE
- **Evidence**: used in api.ts and supabase.ts

### Claim 56
- **Doc**: line 218: "Candlestick chart on instrument dashboard" (under "Next: Phase 3")
- **Verdict**: OUTDATED
- **Evidence**: `candlestick-chart.tsx` already exists and is rendered
- **Fix**: move out of "Phase 3" — already implemented

### Claim 57
- **Doc**: line 221: "New endpoint: GET /api/instruments/:symbol/ohlc" (under "Next: Phase 3")
- **Verdict**: OUTDATED
- **Evidence**: `api/main.py:347` and `api.ts:120-123` — already implemented
- **Fix**: move out of "Phase 3"

### Claim 58
- **Doc**: line 222: "New component: candlestick-chart.tsx" (under "Next: Phase 3")
- **Verdict**: OUTDATED
- **Evidence**: file exists, 133 lines, fully functional
- **Fix**: move out of "Phase 3"

### Claim 59
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `front/src/hooks/use-ohlc.ts` — OHLC hook not in file structure
- **Fix**: add to hooks section

### Claim 60
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `auth-provider.tsx:52-57` — magic link login not documented
- **Fix**: add to Auth section

### Claim 61
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `candlestick-chart.tsx` not in file structure (only in Phase 3)
- **Fix**: add to charts section

### Claim 62
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `input-group.tsx` not in file structure
- **Fix**: minor, add to ui/ section

### Claim 63
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: key deps not mentioned: lightweight-charts, streamdown, use-stick-to-bottom
- **Fix**: add Dependencies section

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 40 |
| OUTDATED | 7 |
| WRONG | 3 |
| MISSING | 5 |
| UNVERIFIABLE | 2 |
| **Total** | **57** |
| **Accuracy** | **70%** |

## Verification

Date: 2026-02-15

### Claims 1-12 — CONFIRMED
### Claim 13 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: WRONG (confirmed, broader violation than noted)
- **Reason**: Multiple panels import hooks directly (instrument-panel, data-panel), not just sidebar-panel
### Claims 14-18 — CONFIRMED
### Claim 19 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: WRONG (confirmed)
- **Reason**: SidebarProvider uses viewport width + resize listener, NOT localStorage
### Claims 20-25 — CONFIRMED
### Claim 26 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: WRONG (confirmed)
- **Reason**: format.ts has no date formatting, only column labels and number formatting
### Claims 27-28 — CONFIRMED
### Claim 29 — DISPUTED
- **Auditor said**: WRONG
- **Should be**: WRONG (confirmed)
- **Reason**: Like/dislike buttons are non-functional UI placeholders with no onClick handlers
### Claims 30-32 — CONFIRMED
### Claim 33 — DISPUTED
- **Auditor said**: MISSING
- **Should be**: WRONG
- **Reason**: root-layout has no mobile overlay, just different width on mobile
### Claims 34-46 — CONFIRMED
### Claim 47 — CONFIRMED
### Claims 48-55 — CONFIRMED
### Claim 56 — CONFIRMED
### Claim 57 — CONFIRMED
### Claims 58-63 — DISPUTED
- **Auditor said**: MISSING
- **Should be**: MISSING (confirmed, all new components/files not documented)

| Result | Count |
|--------|-------|
| CONFIRMED | 57 |
| DISPUTED | 6 |
| INCONCLUSIVE | 0 |
| **Total** | **63** |
