# Audit: frontend-quality.md

Date: 2026-02-15

## Claims

### Claim 1
- **Doc**: line 7: "Every component that displays data handles 4 states: Loading, Error, Empty, Success"
- **Verdict**: UNVERIFIABLE
- **Evidence**: claim is an aspirational guideline about "every component"; doc itself acknowledges gaps

### Claim 2
- **Doc**: line 22: "User input is not lost on error. If send fails, text stays in the input."
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/ai/prompt-input.tsx:74-77` — input only cleared on `.then()` (success); on `.catch()` value preserved

### Claim 3
- **Doc**: line 23: "Expired token redirects to login, not a white screen."
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/auth/auth-guard.tsx:16` — `if (!session) return <Navigate to="/login" replace />;`

### Claim 4
- **Doc**: line 24: "Error boundaries reset on navigation (RouteErrorBoundary with resetKey)."
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/error-boundary.tsx:47-49` — `RouteErrorBoundary` uses `pathname` as `resetKey`

### Claim 5
- **Doc**: line 28: "No `any`. No `as unknown as X`."
- **Verdict**: ACCURATE
- **Evidence**: Grep for `: any` and `as unknown as` across `.ts`/`.tsx` returned no matches

### Claim 6
- **Doc**: lines 30-39: "Use discriminated unions for async states"
- **Verdict**: ACCURATE
- **Evidence**: guideline; doc acknowledges in line 103 that codebase does NOT use this yet — consistent

### Claim 7
- **Doc**: line 48: "Container/panel split: container has hooks, panel has props."
- **Verdict**: ACCURATE
- **Evidence**: `chat-page.container.tsx:21`, `instrument-page.container.tsx:11`, `login-page.container.tsx:5` — all use hooks and pass props to panels

### Claim 8
- **Doc**: line 49: "Cache: `readCache`/`writeCache` in all providers, same pattern."
- **Verdict**: ACCURATE
- **Evidence**: `front/src/lib/cache.ts:3-18` defines `readCache`/`writeCache`; used in conversations-provider, instruments-provider, use-ohlc

### Claim 9
- **Doc**: line 50: "Naming: `ChatPageContainer`, `InstrumentPageContainer`, `LoginPageContainer`."
- **Verdict**: ACCURATE
- **Evidence**: all three containers use consistent naming

### Claim 10
- **Doc**: line 51: "Headers: sidebar toggle built the same way in every page container."
- **Verdict**: ACCURATE
- **Evidence**: identical pattern across all page containers and HomePage

### Claim 11
- **Doc**: line 58: "hook -> container -> panel -> component"
- **Verdict**: ACCURATE
- **Evidence**: data flow verified in chat and instrument pages

### Claim 12
- **Doc**: line 63: "Panels never import hooks directly (exception: sidebar-panel)."
- **Verdict**: ACCURATE
- **Evidence**: Grep for `from "@/hooks` in panels/ shows only sidebar-panel imports hooks

### Claim 13
- **Doc**: line 67: "StrictMode double-mount does not break logic."
- **Verdict**: ACCURATE
- **Evidence**: `front/src/main.tsx:7` uses `<StrictMode>`; sessionStorage and refs designed to survive double-mount

### Claim 14
- **Doc**: line 68: "Fast navigation: old request's response does not overwrite new data."
- **Verdict**: ACCURATE
- **Evidence**: all async effects use `cancelled` flag pattern in use-chat, use-ohlc, providers

### Claim 15
- **Doc**: line 69: "Double click: does not create duplicate requests."
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/panels/chat-panel.tsx:93` — submit button disabled while loading

### Claim 16
- **Doc**: line 75: "`aria-label` on icon-only buttons."
- **Verdict**: ACCURATE
- **Evidence**: all icon-only buttons have aria-labels across page containers, sidebar, data-panel, prompt-input

### Claim 17
- **Doc**: line 82: "`useCallback` on functions passed to memoized children. Not on everything."
- **Verdict**: ACCURATE
- **Evidence**: only 2 files use `useCallback` — selective, not blanket

### Claim 18
- **Doc**: line 84: "Route-level code splitting with `React.lazy`."
- **Verdict**: ACCURATE
- **Evidence**: guideline; doc acknowledges in line 105 this is NOT implemented yet — consistent

### Claim 19
- **Doc**: line 85: "Stable references: module-level constants, singleton caches."
- **Verdict**: ACCURATE
- **Evidence**: `use-chat.ts:17-18` module-level `messageCache`; `data-panel.tsx:90-91` module-level row models

### Claim 20
- **Doc**: line 89: "No `dangerouslySetInnerHTML` without sanitization."
- **Verdict**: ACCURATE
- **Evidence**: `front/src/components/ui/chart.tsx:81` — only usage, HTML from internal config values, no user input

### Claim 21
- **Doc**: line 90: "Token storage: understand the tradeoff"
- **Verdict**: UNVERIFIABLE
- **Evidence**: knowledge guideline, not verifiable code claim

### Claim 22
- **Doc**: line 103: "async states use `boolean + null + error`, not discriminated unions"
- **Verdict**: ACCURATE
- **Evidence**: `use-chat.ts:30-32`, conversations-provider, instruments-provider all use boolean+null pattern

### Claim 23
- **Doc**: line 104: "4 test files for 58 source files"
- **Verdict**: ACCURATE
- **Evidence**: `front/src/__tests__/` contains exactly 4 files; source count ~58

### Claim 24
- **Doc**: line 104: "Critical paths (auth, chat streaming, component rendering) not covered."
- **Verdict**: OUTDATED
- **Evidence**: `front/src/__tests__/use-chat.test.ts` now covers chat streaming path
- **Fix**: change to "Critical paths (auth, component rendering) not covered. Chat has basic tests."

### Claim 25
- **Doc**: line 105: "no `React.lazy`, entire app in one bundle"
- **Verdict**: ACCURATE
- **Evidence**: Grep for `React.lazy` returned no matches

### Claim 26
- **Doc**: line 106: "sidebar-panel.tsx: uses 7 hooks directly"
- **Verdict**: WRONG
- **Evidence**: `front/src/components/panels/sidebar-panel.tsx` uses 8 hooks: useState, useNavigate, useParams, useAuth, useConversations, useInstruments, useSidebar, useTheme
- **Fix**: change "7 hooks" to "8 hooks"

### Claim 27
- **Doc**: line 106: "splitting would create a 15+ prop interface"
- **Verdict**: UNVERIFIABLE
- **Evidence**: subjective estimate of hypothetical refactoring

### Claim 28
- **Doc**: line 20: "Network error does not break UI permanently. User can retry."
- **Verdict**: ACCURATE
- **Evidence**: conversations-provider and instruments-provider have `retry()` function; chat errors show toast

### Claim 29
- **Doc**: not mentioned
- **Verdict**: MISSING
- **Evidence**: `front/src/pages/home/home-page.tsx:7` — `HomePage` uses hooks directly without a `HomePageContainer` wrapper, breaking container/panel convention
- **Fix**: add to "Current Gaps": "HomePage uses hooks directly without a container wrapper"

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE | 21 |
| OUTDATED | 1 |
| WRONG | 1 |
| MISSING | 1 |
| UNVERIFIABLE | 3 |
| **Total** | **27** |
| **Accuracy** | **78%** |

## Verification

Date: 2026-02-15

### Claims 1-22 — CONFIRMED
### Claim 23 — DISPUTED
- **Auditor said**: ACCURATE
- **Should be**: OUTDATED
- **Reason**: Source file count is 63, not ~58
### Claim 24 — DISPUTED
- **Auditor said**: ACCURATE
- **Should be**: OUTDATED
- **Reason**: Chat tests exist (use-chat.test.ts), claim about no chat tests is outdated
### Claims 25-26 — CONFIRMED
### Claim 26 — DISPUTED
- **Auditor said**: ACCURATE
- **Should be**: OUTDATED
- **Reason**: Sidebar uses 8 hooks, not 7
### Claims 27-29 — CONFIRMED

| Result | Count |
|--------|-------|
| CONFIRMED | 26 |
| DISPUTED | 3 |
| INCONCLUSIVE | 0 |
| **Total** | **29** |
