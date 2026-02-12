# Frontend: Instrument Workspace Architecture

## Problem

The frontend is a flat chat list. Sidebar shows all conversations, "New chat" always creates NQ. Backend already supports 31 instruments (loaded from Supabase at startup), but the UI has no way to pick or switch instruments.

## Target

Instrument-centric workspace, similar to Claude Projects or Slack workspaces. Each instrument is a workspace with its own chat list, and later — dashboard, chart, backtests.

## Current state

```
Routes:
  /           → ChatPage (new chat)
  /c/:id      → ChatPage (existing chat)

Layout:
  sidebar-panel | chat-panel | data-panel

Sidebar:
  [user menu]
  [+ New chat]        ← hardcodes "NQ"
  [conversation list] ← all conversations, flat

Key files:
  app.tsx                          — BrowserRouter, routes
  components/panels/sidebar-panel  — sidebar with conversation list
  components/conversations/conversations-provider — loads all conversations
  pages/chat/chat-page             — 3-panel layout
  lib/api.ts                       — createConversation(instrument, token)
  types/index.ts                   — Conversation { instrument }
```

The `instrument` field already exists on every conversation. The API's `createConversation` accepts any instrument. The frontend just never lets the user choose.

## Target state

### Routes

```
/                       → redirect to last instrument or /add
/i/:symbol              → instrument dashboard (chat list as primary view)
/i/:symbol/c/:id        → chat within instrument
/add                    → add instrument modal (full page for first-time)
/login                  → login (unchanged)
```

### Navigation model

```
┌──────────────────────────────────────────────────────┐
│ sidebar            │ main area                        │
│                    │                                  │
│ [user menu]        │  On /i/:symbol:                  │
│                    │    instrument header (name, info) │
│ ── instruments ──  │    [+ New chat]                  │
│ [NQ] ← active     │    conversation list (cards)     │
│ [ES]              │                                   │
│ [CL]              │  On /i/:symbol/c/:id:             │
│                    │    chat-panel | data-panel        │
│ [+ Add]            │    (same 3-panel as now, minus   │
│                    │     sidebar conversations)       │
└──────────────────────────────────────────────────────┘
```

**Sidebar changes:**
- Shows user's instruments (icons or short symbols), not conversations
- Active instrument is highlighted
- "+ Add" button at the bottom opens instrument search modal
- User menu stays at top (theme, settings, sign out)

**Instrument dashboard (`/i/:symbol`):**
- Header: instrument name, exchange, description from Supabase
- "New chat" button — creates conversation with this instrument
- List of conversations for this instrument, sorted by `updated_at`
- Each conversation card: title, date, message count
- Click card → navigate to `/i/:symbol/c/:id`

**Chat view (`/i/:symbol/c/:id`):**
- Same layout as current `ChatPage`: chat-panel + data-panel
- Sidebar shows instruments (not conversations) — clicking another instrument navigates away
- Back button in chat header → returns to `/i/:symbol`

### Add instrument modal

Triggered by "+ Add" in sidebar. Modal overlay (not a page, except for first-time users with 0 instruments).

```
┌─────────────────────────────────┐
│ Add instrument                  │
│                                 │
│ [🔍 Search by symbol or name ] │
│                                 │
│ Equity Index Futures            │
│   NQ  E-mini Nasdaq 100   [+]  │
│   ES  E-mini S&P 500      [+]  │
│   YM  E-mini Dow Jones    [+]  │
│                                 │
│ Energy Futures                  │
│   CL  Crude Oil WTI       [+]  │
│   NG  Natural Gas          [+]  │
│   ...                           │
└─────────────────────────────────┘
```

- Source: `GET /api/instruments` (new endpoint, returns all 31)
- Grouped by `category` from Supabase `instruments` table
- Search filters by `symbol` and `name` (client-side, 31 items)
- Already-added instruments show checkmark instead of "+"
- Click "+" → calls `POST /api/user-instruments` → instrument appears in sidebar

### Component changes

**Modified:**

| File | Change |
|------|--------|
| `app.tsx` | New route structure: `/i/:symbol`, `/i/:symbol/c/:id`, `/add` |
| `sidebar-panel.tsx` | Show instruments instead of conversations. Active instrument highlight. "+ Add" button |
| `conversations-provider.tsx` | Filter by current instrument (from route param `:symbol`) |
| `lib/api.ts` | New functions: `listInstruments`, `listUserInstruments`, `addUserInstrument`, `removeUserInstrument`, `listConversations` gets `?instrument=` param |
| `types/index.ts` | New `Instrument` type |

**New:**

| File | Purpose |
|------|---------|
| `pages/instrument/instrument-page.tsx` | Instrument dashboard — header + conversation list |
| `pages/instrument/instrument-page.container.tsx` | Data loading, connects to providers |
| `components/instruments/instruments-provider.tsx` | Context: user's instruments list, add/remove |
| `components/instruments/add-instrument-modal.tsx` | Search + add instrument modal |

### Data model

**New Supabase table: `user_instruments`**

```sql
create table user_instruments (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id),
  instrument text not null,
  added_at   timestamptz not null default now(),

  unique (user_id, instrument)
);

alter table user_instruments enable row level security;

create policy "Users manage own instruments"
  on user_instruments for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
```

**New API endpoints:**

```
GET    /api/instruments              → list all 31 (public, from instrument_full view)
GET    /api/user-instruments         → list user's added instruments
POST   /api/user-instruments         → add instrument { instrument: "ES" }
DELETE /api/user-instruments/:symbol → remove instrument from user's list
```

**Modified endpoint:**

```
GET /api/conversations?instrument=NQ → filter conversations by instrument
```

Currently `list_conversations` in `api/main.py` returns all user conversations. Add optional `instrument` query param:

```python
@app.get("/api/conversations")
def list_conversations(
    instrument: str | None = None,  # new
    user: dict = Depends(get_current_user),
):
    query = db.table("conversations").select("*").eq("user_id", user["sub"]).eq("status", "active")
    if instrument:
        query = query.eq("instrument", instrument)
    ...
```

### Types

```typescript
// types/index.ts

interface Instrument {
  symbol: string;        // "NQ"
  name: string;          // "E-mini Nasdaq 100"
  exchange: string;      // "CME"
  category: string;      // "equity_index"
  tick_size: number;
  tick_value: number;
  notes: string | null;  // rollover warnings etc.
}

interface UserInstrument {
  instrument: string;    // "NQ"
  added_at: string;
}
```

### State management

**`InstrumentsProvider`** — wraps authenticated routes, similar to `ConversationsProvider`:

```
AuthGuard
  └── InstrumentsProvider          ← new, loads user's instruments once
        └── Routes
              /i/:symbol
                └── ConversationsProvider  ← scoped to :symbol
                      └── InstrumentPage or ChatPage
```

Provider loads user instruments on mount. Exposes: `instruments`, `add(symbol)`, `remove(symbol)`.

**`ConversationsProvider`** — becomes instrument-scoped. Reads `:symbol` from route, passes `?instrument=` to API. Re-fetches when symbol changes.

### Navigation flow

1. **User logs in** → redirect to `/` → check user instruments
   - Has instruments → redirect to `/i/{first_instrument}`
   - No instruments → redirect to `/add` (full-page add experience)

2. **User clicks instrument in sidebar** → navigate to `/i/:symbol`
   - Dashboard loads conversations for that instrument

3. **User clicks "+ New chat"** on dashboard → `POST /api/conversations { instrument }` → navigate to `/i/:symbol/c/:id`

4. **User clicks conversation** on dashboard → navigate to `/i/:symbol/c/:id`

5. **User clicks "+ Add" in sidebar** → open modal → select instrument → `POST /api/user-instruments` → instrument appears in sidebar → navigate to `/i/:symbol`

6. **User in chat clicks different instrument in sidebar** → navigate to `/i/:other_symbol` (leaves chat)

## Implementation phases

### Phase 1: Backend

1. Migration: create `user_instruments` table with RLS
2. New endpoints: `/api/instruments`, `/api/user-instruments` CRUD
3. Add `?instrument=` filter to `GET /api/conversations`
4. Tests for new endpoints

### Phase 2: Frontend structure

1. `Instrument` type, API functions in `lib/api.ts`
2. `InstrumentsProvider` — loads user instruments
3. New routes in `app.tsx`
4. Sidebar: instruments instead of conversations
5. `AddInstrumentModal` — search and add
6. `InstrumentPage` — dashboard with conversation list
7. Scope `ConversationsProvider` to current instrument
8. First-time flow: no instruments → `/add`

### Phase 3: Dashboard content (future)

- Instrument info card (contract specs, sessions, holidays)
- Embedded chart (lightweight-charts or TradingView widget)
- Backtest results list
- Saved queries / bookmarks
