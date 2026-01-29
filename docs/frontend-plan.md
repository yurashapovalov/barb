# Frontend + Supabase Integration

## Architecture

```
Vercel (barb.app)          Hetzner (api.barb.app)
┌─────────────────┐        ┌─────────────────┐
│  Vite + React   │──JWT──▶│  FastAPI         │──▶ Gemini
│  shadcn/ui      │◀─resp──│  (validates JWT) │
└────────┬────────┘        └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Supabase       │
│  - Auth         │
│  - conversations│
│  - messages     │
└─────────────────┘
```

- Frontend → Supabase: auth (Google OAuth) + chat history (read/write)
- Frontend → API: chat requests with JWT
- API: validates JWT, processes chat, returns response. Does NOT touch Supabase.

### Auth flow

```
User clicks "Sign in with Google"
  → supabase.auth.signInWithOAuth({ provider: 'google' })
  → Redirect to Google consent screen
  → Google redirects back to barb.app with code
  → Supabase exchanges code for session + JWT
  → Frontend stores session, sends JWT to API
```

### Google OAuth setup (one-time)

1. Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application)
   - Authorized redirect URI: `https://<supabase-project>.supabase.co/auth/v1/callback`
3. Copy Client ID + Client Secret
4. Supabase Dashboard → Authentication → Providers → Google
   - Enable, paste Client ID + Secret

---

## 1. Supabase Schema

### conversations

```sql
create table public.conversations (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  title       text not null default 'New conversation',
  instrument  text not null default 'NQ',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index idx_conversations_user_updated
  on public.conversations (user_id, updated_at desc);
```

### messages

```sql
create table public.messages (
  id               uuid primary key default gen_random_uuid(),
  conversation_id  uuid not null references public.conversations(id) on delete cascade,
  role             text not null check (role in ('user', 'model')),
  content          text not null default '',
  data             jsonb,    -- DataBlock[] from API response (null for user messages)
  cost             jsonb,    -- CostBlock from API response (null for user messages)
  created_at       timestamptz not null default now()
);

create index idx_messages_conversation_created
  on public.messages (conversation_id, created_at asc);
```

### RLS Policies

```sql
alter table public.conversations enable row level security;
alter table public.messages enable row level security;

-- Conversations: users CRUD only their own
create policy "Users select own conversations"
  on public.conversations for select using (auth.uid() = user_id);
create policy "Users insert own conversations"
  on public.conversations for insert with check (auth.uid() = user_id);
create policy "Users update own conversations"
  on public.conversations for update using (auth.uid() = user_id);
create policy "Users delete own conversations"
  on public.conversations for delete using (auth.uid() = user_id);

-- Messages: users CRUD messages in their own conversations
create policy "Users select own messages"
  on public.messages for select
  using (conversation_id in (select id from public.conversations where user_id = auth.uid()));
create policy "Users insert own messages"
  on public.messages for insert
  with check (conversation_id in (select id from public.conversations where user_id = auth.uid()));
create policy "Users delete own messages"
  on public.messages for delete
  using (conversation_id in (select id from public.conversations where user_id = auth.uid()));
```

### Auto-update trigger

```sql
create or replace function public.update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger conversations_updated_at
  before update on public.conversations
  for each row execute function public.update_updated_at();
```

### Design decisions

- `data` JSONB, not a separate table — always loaded with the message
- `role` = `'user' | 'model'` — matches Gemini convention and existing API history format
- Cascade deletes, no soft deletes
- Title defaults to `'New conversation'`, frontend sets from first message

---

## 2. Backend Changes

Minimal. API stays stateless — only adds JWT validation.

### New: `api/auth.py`

```python
from fastapi import HTTPException, Request
import jwt

from api.config import get_settings

def get_current_user(request: Request) -> dict:
    """Validate Supabase JWT from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization token")

    token = auth[7:]
    try:
        return jwt.decode(
            token, get_settings().supabase_jwt_secret,
            algorithms=["HS256"], audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### Modified: `api/main.py`

```python
from api.auth import get_current_user

@app.post("/api/chat")
def chat(request: ChatRequest, user: dict = Depends(get_current_user)) -> ChatResponse:
    log.info("Chat from user %s", user["sub"])
    # ... rest unchanged
```

### Modified: `api/config.py`

```python
class Settings(BaseSettings):
    gemini_api_key: str = ""
    supabase_jwt_secret: str = ""
```

### Modified: `pyproject.toml`

Add `pyjwt>=2.0.0` to dependencies.

### Modified: docker-compose files

Add `SUPABASE_JWT_SECRET` env var to both `docker-compose.yml` and `docker-compose.prod.yml`.

---

## 3. Frontend

### Tech stack

- Vite + React + TypeScript
- React Router
- shadcn/ui + shadcn AI components (Message, Conversation, PromptInput)
- `@supabase/supabase-js`
- Plain `fetch` for API calls

### Project structure

```
web/
  src/
    main.tsx                        # BrowserRouter + AuthProvider
    app.tsx                         # Routes
    lib/
      supabase.ts                   # createClient singleton
      api.ts                        # sendMessage(message, history, instrument, token)
    hooks/
      use-auth.ts                   # { user, session, loading, signIn, signUp, signOut }
      use-chat.ts                   # { messages, send, isLoading, conversationId }
      use-conversations.ts          # { list, create, remove }
    types/
      index.ts                      # Message, Conversation, ChatResponse, DataBlock, CostBlock
    components/
      auth/
        login-page.tsx              # Container: "Sign in with Google" button + useAuth
        auth-guard.tsx              # Redirect to /login if no session
      chat/
        chat-page.tsx               # Container: orchestrates useChat
        message-list.tsx            # Presentational: renders messages
        message-item.tsx            # Presentational: wraps shadcn Message
        data-display.tsx            # Presentational: table or scalar
        prompt-input.tsx            # Presentational: wraps shadcn PromptInput
      sidebar/
        sidebar.tsx                 # Conversation list + new chat
        conversation-item.tsx       # Single row
      layout/
        root-layout.tsx             # Sidebar + Outlet
```

### Routes

| Route | Component | Auth |
|-------|-----------|------|
| `/login` | LoginPage | No |
| `/` | ChatPage (new conversation) | Yes |
| `/c/:id` | ChatPage (existing conversation) | Yes |

### Component philosophy

**Containers** (hooks, state, events): ChatPage, LoginPage, AuthGuard, RootLayout

**Presentational** (props in, callbacks out): MessageList, MessageItem, DataDisplay, PromptInput, ConversationItem, Sidebar

Logic lives in hooks. Components only render.

### State management

- `AuthProvider` context — the only global state (user + session)
- `useChat` / `useConversations` — local hooks with useState
- No zustand, no Redux, no global store

### Hooks

**`useAuth()`** — wraps Supabase auth via context

```typescript
{ user, session, loading, signInWithGoogle, signOut }
```

**`useChat(conversationId?)`** — manages one conversation

```typescript
{ messages, isLoading, error, send, conversationId }
```

- On mount with id: fetch messages from Supabase
- `send(text)`: create conversation if new → insert user msg → call API → insert model msg
- Builds `history[]` from local state for API calls

**`useConversations()`** — manages the list

```typescript
{ conversations, loading, create, remove }
```

### Chat flow

```
User types → Enter
  ↓
useChat.send(text)
  ├── No conversationId? → INSERT conversation → navigate /c/:id
  ├── INSERT user message (Supabase)
  ├── Set isLoading = true
  ├── POST /api/chat (message, history, instrument, JWT)
  ├── INSERT model message with data + cost (Supabase)
  └── Set isLoading = false
```

### Types

```typescript
interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'model';
  content: string;
  data: DataBlock[] | null;
  cost: CostBlock | null;
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  instrument: string;
  created_at: string;
  updated_at: string;
}

interface DataBlock {
  query: Record<string, unknown>;
  result: unknown;
  rows: number | null;
  session: string | null;
  timeframe: string | null;
}

interface CostBlock {
  input_tokens: number;
  output_tokens: number;
  thinking_tokens: number;
  cached_tokens: number;
  input_cost: number;
  output_cost: number;
  thinking_cost: number;
  total_cost: number;
}

interface ChatResponse {
  answer: string;
  data: DataBlock[];
  cost: CostBlock;
}
```

Types mirror backend Pydantic models exactly.

---

## 4. Deployment

### Vercel (frontend)

- Root directory: `web/`
- Build: `npm run build` → `dist/`
- SPA rewrite in `vercel.json`: `/(.*) → /index.html`
- Env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`

### DNS

- `barb.app` → Vercel
- `api.barb.app` → 37.27.204.135 (Hetzner)

### Backend

- Add `SUPABASE_JWT_SECRET` to prod env
- CORS already set to `https://barb.app`

---

## 5. Implementation Order

### Phase 1: Google OAuth + Supabase schema
1. Google Cloud Console → create OAuth 2.0 Client ID
   - Authorized redirect URI: `https://<project>.supabase.co/auth/v1/callback`
2. Supabase Dashboard → Authentication → Providers → Google → enable, paste credentials
3. Run SQL (tables, indexes, RLS, trigger) in Supabase SQL Editor
4. Get JWT secret from Supabase Dashboard → Settings → API

### Phase 2: Backend auth
Create `api/auth.py`. Wire into endpoint. Add pyjwt dep. Add env var. Test: no token → 401.

### Phase 3: Frontend scaffold
`npm create vite`, install deps, create structure, lib/supabase.ts, lib/api.ts, types.

### Phase 4: Auth flow
useAuth hook, AuthProvider, LoginPage ("Sign in with Google" button), AuthGuard. Test: OAuth → redirect → session.

### Phase 5: Chat UI
useChat, useConversations, presentational components, sidebar, layout. Test: full flow end-to-end.

### Phase 6: Deploy
Push, connect Vercel, DNS, env vars. Test production.
