# Frontend Code Review

Review of all 62 source files against `docs/barb/frontend-quality.md`.

Date: 2026-02-13
Updated: 2026-02-13

---

## 1. States (Loading / Error / Empty / Success)

Each data-fetching component should handle 4 states. Here's what's missing:

| Component | Loading | Error | Empty | Success |
|-----------|---------|-------|-------|---------|
| AuthGuard | ~~blank screen~~ fixed: spinner | N/A | N/A | OK |
| AuthProvider | OK | logs only, no UI | N/A | OK |
| ConversationsProvider | OK | ~~swallowed~~ fixed: toast | OK (consumers) | OK |
| InstrumentsProvider | OK | ~~swallowed~~ fixed: toast | OK (consumers) | OK |
| ChatPanel | OK (btn disabled) | ~~inline div~~ fixed: toast | ~~none~~ fixed: empty state | OK |
| InstrumentPanel | OK ("Loading...") | ~~none~~ fixed: toast (via provider) | OK | OK |
| DataPanel | N/A (prop) | N/A | OK ("No data.") | OK |
| AddInstrumentModal | OK ("Loading...") | **console.error only** | OK | OK |
| SidebarPanel | **no loading** | ~~none~~ fixed: toast (via providers) | OK (instruments=[]) | OK |
| LoginPage | OK (spinner) | OK | N/A | OK |

**Remaining issues:**
- **AddInstrumentModal** (`add-instrument-modal.tsx:56`): `listInstruments()` failure only logs.
- **SidebarPanel** (`sidebar-panel.tsx`): No loading indicator for instruments/conversations. Shows empty sections until data loads.

---

## 2. Error Recovery

| Requirement | Status | Notes |
|-------------|--------|-------|
| Network error doesn't break UI | ~~Partial~~ OK | Providers expose error + retry; toasts notify user |
| Optimistic rollback | OK | `useChat.send()` removes optimistic messages on error |
| Input preserved on error | OK | PromptInput clears only in `.then()`, not `.catch()` |
| Expired token → login | ~~Partial~~ OK | `checkAuth()` in api.ts detects 401, signs out via supabase |
| Error boundaries reset on nav | OK | `RouteErrorBoundary` uses `pathname` as `resetKey` |

All error recovery issues fixed.

---

## 3. Types

| Requirement | Status | Notes |
|-------------|--------|-------|
| No `any` | OK | Zero `any` types found |
| No `as unknown as X` | ~~Fail~~ OK | Replaced with type guards using `has()` helper |
| Discriminated unions | Skip | Decided to keep boolean+null — data persists across loading/error states in providers |

---

## 4. Consistency

| Requirement | Status | Notes |
|-------------|--------|-------|
| Container/panel split | OK | All pages follow the pattern |
| Cache pattern | OK | `readCache`/`writeCache` in both providers; useChat uses module-level Map (documented reason) |
| Naming | OK | `ChatPageContainer`, `InstrumentPageContainer`, `LoginPageContainer` |
| Headers | OK | Sidebar toggle built the same way everywhere |

No issues.

---

## 5. Data Flow

```
hook → container → panel → component
```

| Requirement | Status | Notes |
|-------------|--------|-------|
| One-direction data flow | OK | |
| Components don't know data source | OK | |
| Panels don't import hooks | OK | Exception: sidebar-panel (documented) |

No issues.

---

## 6. Race Conditions

| Requirement | Status | Notes |
|-------------|--------|-------|
| StrictMode safe | OK | `isSendingRef` + `sentRef` survive double-mount |
| Fast navigation cancellation | OK | `cancelled` flag in all effects |
| Double click prevention | OK | Submit disabled during `isLoading` |

~~**Minor note:** `send` function in `useChat` is not memoized, causing effect re-runs.~~ Fixed: `sendRef` pattern in ChatPageContainer prevents unnecessary re-runs.

---

## 7. Accessibility

~~**5 icon-only buttons missing `aria-label`**~~ — all fixed:

| Button | File | Status |
|--------|------|--------|
| Sidebar toggle (PanelLeftIcon) | `home-page.tsx` | fixed |
| Sidebar toggle (PanelLeftIcon) | `instrument-page.container.tsx` | fixed |
| Sidebar toggle (PanelLeftIcon) | `chat-page.container.tsx` | fixed |
| Menu button (EllipsisIcon) | `chat-page.container.tsx` | fixed |
| Close data panel (XIcon) | `data-panel.tsx` | fixed |

**Other a11y notes:**
- Semantic HTML is generally good — `<button>` for actions, proper heading hierarchy.
- Radix UI primitives handle focus trapping in dialogs/dropdowns.
- `Conversation` component has `role="log"` — good for screen readers.
- Tab navigation should work via shadcn/Radix defaults.

---

## 8. Performance

| Requirement | Status | Notes |
|-------------|--------|-------|
| `useCallback` on passed functions | OK | `handleSelectData` memoized; `sendRef` pattern prevents effect churn |
| Long lists | OK for now | No virtualization, but lists are small |
| Route-level code splitting | Skip | No `React.lazy` — app is small, add when bundle size matters |
| Stable references | OK | Module-level `coreRowModel`, `sortedRowModel`, `messageCache` |

---

## 9. Security

| Requirement | Status | Notes |
|-------------|--------|-------|
| `dangerouslySetInnerHTML` | OK | Only in `chart.tsx` for CSS generation from hardcoded config |
| Token storage | OK | Supabase SDK default (localStorage) — known tradeoff |
| Input encoding | OK | `encodeURIComponent` used in URL params |
| 401 handling | ~~missing~~ OK | `checkAuth()` detects 401, triggers sign-out |

---

## 10. Tests

| Requirement | Status | Notes |
|-------------|--------|-------|
| Critical paths covered | Partial | API + useChat covered; auth flow, component rendering NOT covered |
| Tests check behavior | OK | Tests assert on callbacks, messages, errors |
| Edge cases | OK | Malformed JSON, missing fields, error responses |

**4 test files for 58 source files (7% coverage by file count).**

Covered:
- `api.test.ts` — API functions + SSE streaming (thorough)
- `parse-content.test.ts` — content parsing (thorough)
- `use-chat.test.ts` — chat hook lifecycle (good) — ~~bug: missing `instrument` param~~ fixed
- `use-theme.test.ts` — theme switching (good)

Not covered:
- Auth flow (sign in, sign out, token expiry)
- Error boundaries (error rendering, reset on navigation)
- Component rendering (ChatPanel, InstrumentPanel, etc.)
- Provider behavior (ConversationsProvider, InstrumentsProvider)
- Data panel (sorting, chart rendering)

---

## 11. Dead Code

~~**Unused UI components:**~~ Deleted: `card.tsx`, `drawer.tsx`.

---

## Summary

### Fixed (this pass)
1. ~~use-chat.test.ts missing `instrument` param~~ — added to all test calls
2. ~~5 icon-only buttons missing `aria-label`~~ — all labeled
3. ~~Providers swallow errors~~ — error state + retry exposed; toasts for all errors
4. ~~No 401 handling~~ — `checkAuth()` in api.ts with dynamic supabase import
5. ~~ChatPanel no empty state~~ — ConversationEmptyState added
6. ~~AuthGuard blank screen~~ — centered spinner
7. ~~`as unknown as` casts~~ — replaced with type guards
8. ~~sendRef pattern~~ — stable effect in ChatPageContainer
9. ~~Dead UI components~~ — card.tsx, drawer.tsx deleted
10. ~~Inline error displays~~ — replaced with sonner toasts

### Remaining
- **AddInstrumentModal**: `listInstruments()` failure only logs
- **SidebarPanel**: no loading indicator for instruments/conversations
- **Test coverage**: 4 files for 58 source files — critical paths (auth, components) not covered
- **Discriminated unions**: decided to keep boolean+null (data persists across states)
- **Code splitting**: skip until bundle size matters
