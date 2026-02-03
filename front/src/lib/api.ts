import type {
  Conversation,
  Message,
  SSEDataBlockEvent,
  SSEDoneEvent,
  SSEErrorEvent,
  SSEPersistEvent,
  SSETextDeltaEvent,
  SSETitleUpdateEvent,
  SSEToolEndEvent,
  SSEToolStartEvent,
} from "@/types";

const API_URL = import.meta.env.VITE_API_URL ?? "";

function authHeaders(token: string) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function createConversation(
  instrument: string,
  token: string,
): Promise<Conversation> {
  const res = await fetch(`${API_URL}/api/conversations`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ instrument }),
  });
  return handleResponse<Conversation>(res);
}

export async function listConversations(
  token: string,
): Promise<Conversation[]> {
  const res = await fetch(`${API_URL}/api/conversations`, {
    method: "GET",
    headers: authHeaders(token),
  });
  return handleResponse<Conversation[]>(res);
}

export async function deleteConversation(
  conversationId: string,
  token: string,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/conversations/${conversationId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
}

export async function getMessages(
  conversationId: string,
  token: string,
): Promise<Message[]> {
  const res = await fetch(`${API_URL}/api/conversations/${conversationId}/messages`, {
    headers: authHeaders(token),
  });
  return handleResponse<Message[]>(res);
}

export interface StreamCallbacks {
  onToolStart?: (event: SSEToolStartEvent) => void;
  onToolEnd?: (event: SSEToolEndEvent) => void;
  onDataBlock?: (event: SSEDataBlockEvent) => void;
  onTextDelta?: (event: SSETextDeltaEvent) => void;
  onDone?: (event: SSEDoneEvent) => void;
  onPersist?: (event: SSEPersistEvent) => void;
  onTitleUpdate?: (event: SSETitleUpdateEvent) => void;
  onError?: (event: SSEErrorEvent) => void;
}

export async function sendMessageStream(
  conversationId: string,
  message: string,
  token: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ conversation_id: conversationId, message }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  if (!res.body) {
    throw new Error("Response body is null");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE messages are separated by double newlines
    const messages = buffer.split("\n\n");
    buffer = messages.pop() ?? "";

    for (const msg of messages) {
      if (!msg.trim()) continue;

      let eventType = "";
      let dataStr = "";

      for (const line of msg.split("\n")) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7);
        } else if (line.startsWith("data: ")) {
          dataStr = line.slice(6);
        }
      }

      if (!eventType || !dataStr) continue;

      let data: unknown;
      try {
        data = JSON.parse(dataStr);
      } catch {
        continue;
      }

      const obj = data as Record<string, unknown>;
      switch (eventType) {
        case "tool_start":
          if (obj.tool_name) callbacks.onToolStart?.(obj as unknown as SSEToolStartEvent);
          break;
        case "tool_end":
          if (obj.tool_name) callbacks.onToolEnd?.(obj as unknown as SSEToolEndEvent);
          break;
        case "data_block":
          callbacks.onDataBlock?.(obj as unknown as SSEDataBlockEvent);
          break;
        case "text_delta":
          if (typeof obj.delta === "string") callbacks.onTextDelta?.(obj as unknown as SSETextDeltaEvent);
          break;
        case "done":
          if (typeof obj.answer === "string") callbacks.onDone?.(obj as unknown as SSEDoneEvent);
          break;
        case "persist":
          callbacks.onPersist?.(obj as unknown as SSEPersistEvent);
          break;
        case "title_update":
          if (typeof obj.title === "string") callbacks.onTitleUpdate?.(obj as unknown as SSETitleUpdateEvent);
          break;
        case "error":
          if (typeof obj.error === "string") callbacks.onError?.(obj as unknown as SSEErrorEvent);
          break;
      }
    }
  }
}
