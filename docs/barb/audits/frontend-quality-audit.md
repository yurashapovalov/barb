# Audit: frontend-quality.md

**Date**: 2026-02-16
**Claims checked**: 42
**Correct**: 37 | **Wrong**: 2 | **Outdated**: 0 | **Unverifiable**: 3

## Issues

### [WRONG] dangerouslySetInnerHTML without sanitization exists in chart.tsx
- **Doc says**: "No `dangerouslySetInnerHTML` without sanitization."
- **Code says**: `chart.tsx` (shadcn/ui component) uses `dangerouslySetInnerHTML` on line 81 to inject CSS variables from code-defined config. No explicit sanitization, but inputs are not user-controlled — they come from `ChartConfig` objects defined in code. Low risk but contradicts the absolute "No" statement.
- **File**: `front/src/components/ui/chart.tsx:81`

### [WRONG] Test file count: "4 test files for 63 source files" — source count is 58, not 63
- **Doc says**: "4 test files for 63 source files"
- **Code says**: There are 4 test files (correct) and 63 total `.ts`/`.tsx` files, but only 58 are non-test source files (excluding 4 test files + `test-setup.ts`). The doc implies 63 source files being tested, but 63 includes the test files themselves.
- **File**: `front/src/__tests__/` (4 files), `front/src/` (63 total, 58 non-test)

## All Claims Checked

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every component that displays data handles 4 states: Loading, Error, Empty, Success | CORRECT | `instrument-panel.tsx` shows loading spinner (line 57-59), conversations loading (line 62-63), empty state (line 80-82), and data (line 54-56). `chat-panel.tsx` shows empty state (line 43-47), messages (line 49-83), loading in submit button (line 93). Providers handle loading/error/data states. |
| 2 | Network error does not break UI permanently, user can retry without reload | CORRECT | Providers (`conversations-provider.tsx:70-74`, `instruments-provider.tsx:51-55`) expose `retry()`. API errors are caught and shown via `toast.error()`. |
| 3 | Optimistic data rolls back on error | CORRECT | `use-chat.ts:258` — on error, both optimistic user message and assistant message are removed: `prev.filter((m) => m.id !== userMsg.id && m.id !== assistantId)` |
| 4 | User input is not lost on error — if send fails, text stays in the input | CORRECT | `prompt-input.tsx:74-78` — `onSubmit` returns a Promise; `.then()` clears input, `.catch()` only logs. If `send()` throws, input is preserved. |
| 5 | Expired token redirects to login, not a white screen | CORRECT | `api.ts:25-31` — `checkAuth()` on 401 calls `supabase.auth.signOut()` which triggers `onAuthStateChange`, sets session to null. `auth-guard.tsx:16` — `!session` renders `<Navigate to="/login" />`. |
| 6 | Error boundaries reset on navigation (RouteErrorBoundary with resetKey) | CORRECT | `error-boundary.tsx:47-50` — `RouteErrorBoundary` uses `pathname` as `resetKey`. `ErrorBoundary.componentDidUpdate` (line 21-24) resets error when `resetKey` changes. |
| 7 | No `any` type usage | CORRECT | Grep for `: any`, `<any>`, `any[]`, `any)` across all `.ts`/`.tsx` files returns zero matches. |
| 8 | No `as unknown as X` usage | CORRECT | Grep for `as unknown as` returns zero matches. |
| 9 | No `dangerouslySetInnerHTML` without sanitization | WRONG | `chart.tsx:81` uses `dangerouslySetInnerHTML` for CSS injection. Input is code-defined config, not user input — safe in practice, but contradicts the absolute claim. |
| 10 | Async states use `boolean + null + error`, not discriminated unions | CORRECT | `conversations-provider.tsx:19-25`, `instruments-provider.tsx:19-25`, `use-chat.ts:30-32` all use `useState<T[]>`, `useState(boolean)`, `useState<string \| null>` pattern. |
| 11 | Discriminated union gap documented — provider data persists across loading/error states | CORRECT | Providers keep data in state even during loading/error. `conversations-provider.tsx:57-68` (refresh) updates data on success but doesn't clear on loading. |
| 12 | Types express domain concepts: Instrument, Conversation, Message | CORRECT | `types/index.ts` defines `Instrument`, `UserInstrument`, `Message`, `Conversation`, `DataBlock`, `UsageBlock` — all domain types. |
| 13 | Container/panel split: container has hooks, panel has props | CORRECT | `ChatPageContainer` (hooks) renders `ChatPage` (props); `InstrumentPageContainer` (hooks) renders `InstrumentPanel` (props); `LoginPageContainer` (hooks) renders `LoginPage` (props). |
| 14 | Cache: `readCache`/`writeCache` in all providers, same pattern | CORRECT | `conversations-provider.tsx:6,35`, `instruments-provider.tsx:6,35`, `use-ohlc.ts:4,31` all use `readCache`/`writeCache` from `lib/cache.ts`. |
| 15 | Naming: `ChatPageContainer`, `InstrumentPageContainer`, `LoginPageContainer` — consistent | CORRECT | Confirmed in `chat-page.container.tsx:21`, `instrument-page.container.tsx:11`, `login-page.container.tsx:5`. |
| 16 | Sidebar toggle built the same way in every page container | CORRECT | `ChatPageContainer:95-98`, `InstrumentPageContainer:30-33`, `HomePage:12-15` all use identical pattern: `!sidebarOpen && <Button variant="ghost" size="icon-sm" onClick={toggleSidebar} aria-label="Open sidebar"><PanelLeftIcon /></Button>` |
| 17 | Data flows: hook -> container -> panel -> component | CORRECT | `ChatPageContainer` uses `useChat` hook, passes data to `ChatPage`, which passes to `ChatPanel`/`DataPanel`. |
| 18 | Components don't know where data comes from | CORRECT | `ChatPage`, `InstrumentPanel`, `HomePanel`, `LoginPage` all receive data via props, no direct API/hook imports. |
| 19 | Panels never import hooks directly (exception: sidebar-panel, documented) | CORRECT | Grep for `import.*from.*hooks/` in `components/panels/` shows only `sidebar-panel.tsx` imports hooks directly. `chat-panel.tsx` imports `type ChatState` (type-only, not a hook call). |
| 20 | sidebar-panel.tsx uses 8 hooks directly | CORRECT | `useState`, `useNavigate`, `useParams`, `useAuth`, `useConversations`, `useInstruments`, `useSidebar`, `useTheme` — exactly 8 hooks at `sidebar-panel.tsx:31-38`. |
| 21 | StrictMode double-mount does not break logic | CORRECT | `main.tsx:7` uses `<StrictMode>`. `chat-page.container.tsx:33` reads initial message from `sessionStorage` (survives remount). `sentRef` persists across StrictMode unmount/remount. Providers use `cancelled` flag pattern. |
| 22 | Fast navigation: old request's response does not overwrite new data (cleanup + cancelled flag) | CORRECT | `use-chat.ts:60,82`, `conversations-provider.tsx:29,46`, `instruments-provider.tsx:29,46`, `use-ohlc.ts:26,40` all use `let cancelled = false` / `return () => { cancelled = true }` pattern. |
| 23 | Double click: does not create duplicate requests (disable button while loading) | CORRECT | `chat-panel.tsx:93` — submit button `disabled={isEmpty \|\| isLoading}`. `login-page.tsx:69` — magic link button `disabled={!isValidEmail \|\| sending}`. |
| 24 | Semantic HTML: `<button>` for actions, `<a>` for navigation | CORRECT | `instrument-panel.tsx:67-69` uses `<button>` for clickable items. Navigation uses `useNavigate` programmatically. `login-page.tsx:44` uses `<Button>` for actions. |
| 25 | `aria-label` on icon-only buttons | CORRECT | All icon-only buttons have aria-labels: "Open sidebar", "Collapse sidebar", "Close panel", "Chat options", "Submit" — verified across 7 instances in 6 files. |
| 26 | `useCallback` on functions passed to memoized children, not on everything | CORRECT | `chat-page.container.tsx:85` — `useCallback` on `handleSelectData`. `sidebar-provider.tsx:17-18` — `useCallback` on `toggle` and `close`. Only used where needed, not everywhere. |
| 27 | Route-level code splitting with `React.lazy` | CORRECT (gap) | No `React.lazy` usage found. Doc lists this under "Performance" aspirations but also lists it under "Current Gaps" (line 105). |
| 28 | Stable references: module-level constants, singleton caches | CORRECT | `use-chat.ts:17` — `const messageCache = new Map()`. `data-panel.tsx:90-91` — `const coreRowModel = getCoreRowModel()`, `const sortedRowModel = getSortedRowModel()`. |
| 29 | No `dangerouslySetInnerHTML` without sanitization (Security section) | WRONG | See issue above. `chart.tsx:81` uses it. Safe in practice but exists. |
| 30 | Token storage comment about XSS/CSRF tradeoff | UNVERIFIABLE | Supabase JS client handles token storage internally. `supabase.ts` creates client with default config. The tradeoff is architectural knowledge, not verifiable from code alone. |
| 31 | Tests: 4 test files for 63 source files | WRONG | 4 test files correct. But there are 58 non-test source files, not 63. The total of 63 includes 4 test files + `test-setup.ts`. |
| 32 | Auth and component rendering not covered in tests | CORRECT | Test files: `api.test.ts`, `use-chat.test.ts`, `parse-content.test.ts`, `use-theme.test.ts`. No auth or component rendering tests. |
| 33 | Chat streaming has basic tests | CORRECT | `use-chat.test.ts` tests the `useChat` hook with mocked `sendMessageStream`. `api.test.ts` tests SSE parsing. |
| 34 | No `React.lazy`, entire app in one bundle | CORRECT | Grep for `React.lazy` returns zero matches. All routes in `app.tsx` use direct imports. |
| 35 | HomePage uses hooks directly without container wrapper | CORRECT | `home-page.tsx:7` — `HomePage` calls `useSidebar()` directly (line 8). No `HomePageContainer` exists. |
| 36 | sidebar-panel exception — splitting would create 15+ prop interface | UNVERIFIABLE | The 15+ prop count is a design judgment. The sidebar has user info, theme, instruments list, conversations list, navigation, and modal state — plausibly 15+ props if decomposed, but exact count is subjective. |
| 37 | Focus management: focus is not lost after navigation or modal close | UNVERIFIABLE | No explicit `focus()` calls or focus trap implementations found. React Router and Radix Dialog handle focus natively. Cannot fully verify without runtime testing. |
| 38 | User input encoded before inserting into URL | CORRECT | `api.ts:67` — `encodeURIComponent(instrument)` for query params. `api.ts:121,150` — `encodeURIComponent(symbol)` for URL path segments. |
| 39 | Keyboard: all interactive elements reachable via Tab | CORRECT | All interactive elements use `<Button>`, `<button>`, `<input>`, `<textarea>` — natively focusable. Radix UI components (DropdownMenu, Dialog) handle keyboard navigation. |
| 40 | Data flow is one direction | CORRECT | Container components pass data down via props. Child components use callbacks (onSend, onSelectData, onClose) to communicate up. No bidirectional data flow. |
| 41 | `readCache`/`writeCache` pattern consistent across providers | CORRECT | All three data-fetching providers use identical pattern: `readCache` for initial state, `writeCache` after fetch, `cancelled` flag for cleanup. |
| 42 | Error boundaries exist with recovery | CORRECT | `error-boundary.tsx:14-50` — `ErrorBoundary` class component with reload button. `RouteErrorBoundary` resets on navigation. Top-level `ErrorBoundary` wraps entire app in `app.tsx:20`. |
