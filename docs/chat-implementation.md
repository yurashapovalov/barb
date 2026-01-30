# Chat Implementation

Wire up frontend chat UI to backend `POST /api/chat`.

## Current state

- Backend `POST /api/chat` — non-streaming, returns full JSON `ChatResponse`
- Frontend `sendMessage()` in `lib/api.ts` — ready
- Auth token: `useAuth().session.access_token`
- UI components: Conversation, Message, PromptInput (shadcn AI)
- Chat panel has hardcoded demo messages, `handleSubmit` is TODO

## Approach

Custom `useChat` hook. No Vercel AI SDK `useChat()` — it expects a streaming endpoint, our backend returns plain JSON.

## Steps

### 1. Backend: `GET /api/conversations/{id}/messages`

`api/main.py` — new endpoint. Returns `list[Message]` for a conversation. Verify user ownership via JWT.

### 2. Frontend API: `getMessages()`

`front/src/lib/api.ts`:
```ts
export async function getMessages(
  conversationId: string,
  token: string,
): Promise<Message[]> {
  const res = await fetch(`${API_URL}/api/conversations/${conversationId}/messages`, {
    headers: authHeaders(token),
  });
  return handleResponse<Message[]>(res);
}
```

### 3. Hook: `use-chat.ts`

`front/src/hooks/use-chat.ts`:

```ts
interface UseChatParams {
  conversationId: string | undefined;
  token: string;
  onConversationCreated?: (id: string) => void;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  send: (text: string) => void;
}
```

Behavior:
- On mount with `conversationId` — load history via `getMessages()`
- `send(text)`:
  1. If no `conversationId` — call `createConversation()`, then `onConversationCreated(id)`
  2. Optimistically add user message to `messages[]`
  3. Set `isLoading = true`
  4. Call `sendMessage(conversationId, text, token)`
  5. Append assistant message from response
  6. Set `isLoading = false`
- On error — set `error`, remove optimistic message

### 4. Wire up `chat-panel.tsx`

- Remove hardcoded demo messages
- Accept `conversationId`, `token`, `onConversationCreated` as props
- Use `useChat` hook
- Map `messages` to `<Message>` + `<MessageContent>` + `<MessageResponse>`
- `PromptInput.onSubmit` calls `send()`
- Show loading state while `isLoading`

### 5. Route params

`chat-page.container.tsx`:
- Read `useParams().id` as `conversationId`
- Read `useAuth()` for token
- `onConversationCreated` — call `navigate(`/c/${id}`)`
- Pass everything to `ChatPage` -> `ChatPanel`

## Files

| File | Change |
|------|--------|
| `api/main.py` | Add GET messages endpoint |
| `front/src/lib/api.ts` | Add `getMessages()` |
| `front/src/hooks/use-chat.ts` | New hook |
| `front/src/components/panels/chat-panel.tsx` | Wire up, remove demo |
| `front/src/pages/chat/chat-page.tsx` | Accept + pass `conversationId` |
| `front/src/pages/chat/chat-page.container.tsx` | Read route params, auth |

## NOT now

- Streaming responses
- Sidebar conversation list
- Data panel (query results)
- Tool call UI
- Error boundaries

## Verification

1. Open `/` — empty chat with input
2. Type message — user bubble appears, loading, then assistant bubble
3. URL changes to `/c/{id}` after first message
4. Refresh page — messages load from API
5. Open `/c/{id}` directly — loads conversation history
