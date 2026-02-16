# Frontend Quality Checklist

Code quality bar for the frontend. Every file, every PR.

## States

Every component that displays data handles 4 states:

| State | What user sees |
|-------|---------------|
| Loading | Skeleton, spinner, or placeholder |
| Error | What happened + how to recover |
| Empty | Data loaded, nothing to show |
| Success | Data rendered |

If any state is missing, the user sees a blank screen or a stuck spinner.

## Error Recovery

- Network error does not break UI permanently. User can retry without page reload.
- Optimistic data rolls back on error.
- User input is not lost on error. If send fails, text stays in the input.
- Expired token redirects to login, not a white screen.
- Error boundaries reset on navigation (RouteErrorBoundary with resetKey).

## Types

No `any`. No `as unknown as X`.

Use discriminated unions for async states:

```typescript
// Bad — 4 booleans = 16 combinations, 12 are invalid
{ loading: boolean; error: string | null; data: T | null }

// Good — 3 states, all valid
| { status: "loading" }
| { status: "error"; error: string }
| { status: "success"; data: T }
```

Types express domain concepts (Instrument, Conversation, Message), not implementation details.

## Consistency

One pattern — everywhere:

- Container/panel split: container has hooks, panel has props. All pages follow this.
- Cache: `readCache`/`writeCache` in all providers, same pattern.
- Naming: `ChatPageContainer`, `InstrumentPageContainer`, `LoginPageContainer`. Not a mix.
- Headers: sidebar toggle built the same way in every page container.

New developer learns one file, understands the rest without explanation.

## Data Flow

```
hook → container → panel → component
```

- Data flows in one direction.
- Components don't know where data comes from (API, cache, mock).
- Panels never import hooks directly (exception: sidebar-panel, documented).

## Race Conditions

- StrictMode double-mount does not break logic. No one-shot ref flags consumed on first mount.
- Fast navigation: old request's response does not overwrite new data (cleanup + cancelled flag in effects).
- Double click: does not create duplicate requests (disable button while loading, or guard in handler).

## Accessibility

- Semantic HTML: `<button>` for actions, `<a>` for navigation, headings in order.
- Keyboard: all interactive elements reachable via Tab.
- `aria-label` on icon-only buttons.
- Focus management: focus is not lost after navigation or modal close.

## Performance

Intentional, not premature:

- `useCallback` on functions passed to memoized children. Not on everything.
- Long lists: virtualization or pagination, not 1000 DOM nodes.
- Route-level code splitting with `React.lazy`.
- Stable references: module-level constants, singleton caches.

## Security

- No `dangerouslySetInnerHTML` without sanitization.
- Token storage: understand the tradeoff (localStorage = XSS risk, httpOnly cookie = CSRF risk).
- User input encoded before inserting into URL or HTML.

## Tests

- Critical paths covered: auth flow, send message, error recovery.
- Tests check behavior, not implementation. "User sees error message", not "setState called with argument".
- Edge cases: empty data, network error, timeout, rapid navigation.

## Current Gaps

Known deviations from this checklist (update as we fix them):

- **Discriminated unions**: async states use `boolean + null + error`, not discriminated unions. Decided to keep this pattern because provider data (conversations, instruments) persists across loading/error states — a pure discriminated union where data only exists in "success" doesn't fit when you want to show stale cached data during refresh.
- **Tests**: 4 test files for 63 source files. Auth and component rendering not covered (chat streaming has basic tests).
- **Code splitting**: no `React.lazy`, entire app in one bundle. App is small — add when bundle size becomes a problem.
- **sidebar-panel.tsx**: uses 8 hooks directly (useState, useNavigate, useParams, useAuth, useConversations, useInstruments, useSidebar, useTheme) instead of receiving props. Documented exception — splitting would create a 15+ prop interface for no real benefit.
- **HomePage**: uses hooks directly without a container wrapper, unlike other pages.
