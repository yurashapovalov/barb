import type {
  Conversation,
  Instrument,
  Message,
  SSEDataBlockEvent,
  SSEDoneEvent,
  SSEErrorEvent,
  SSEPersistEvent,
  SSETextDeltaEvent,
  SSETitleUpdateEvent,
  SSEToolEndEvent,
  SSEToolStartEvent,
  UserInstrument,
} from "@/types";

const API_URL = import.meta.env.VITE_API_URL ?? "";

function authHeaders(token: string) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function checkAuth(res: Response): Promise<void> {
  if (res.status === 401) {
    const { supabase } = await import("@/lib/supabase");
    await supabase.auth.signOut();
    throw new Error("Session expired");
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  await checkAuth(res);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

async function handleVoidResponse(res: Response): Promise<void> {
  await checkAuth(res);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
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
  instrument?: string,
): Promise<Conversation[]> {
  const url = instrument
    ? `${API_URL}/api/conversations?instrument=${encodeURIComponent(instrument)}`
    : `${API_URL}/api/conversations`;
  const res = await fetch(url, {
    method: "GET",
    headers: authHeaders(token),
  });
  return handleResponse<Conversation[]>(res);
}

export async function removeConversation(
  conversationId: string,
  token: string,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/conversations/${conversationId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  await handleVoidResponse(res);
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

// --- Instruments ---

export async function listInstruments(
  search?: string,
  category?: string,
): Promise<Instrument[]> {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (category) params.set("category", category);
  const qs = params.toString();
  const res = await fetch(`${API_URL}/api/instruments${qs ? `?${qs}` : ""}`);
  return handleResponse<Instrument[]>(res);
}

export interface OHLCBar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export async function getOHLC(symbol: string): Promise<OHLCBar[]> {
  const res = await fetch(`${API_URL}/api/instruments/${encodeURIComponent(symbol)}/ohlc`);
  return handleResponse<OHLCBar[]>(res);
}

export async function listUserInstruments(
  token: string,
): Promise<UserInstrument[]> {
  const res = await fetch(`${API_URL}/api/user-instruments`, {
    headers: authHeaders(token),
  });
  return handleResponse<UserInstrument[]>(res);
}

export async function addUserInstrument(
  symbol: string,
  token: string,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/user-instruments`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ instrument: symbol }),
  });
  await handleVoidResponse(res);
}

export async function removeUserInstrument(
  symbol: string,
  token: string,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/user-instruments/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  await handleVoidResponse(res);
}

// --- SSE type guards ---

function has<K extends string>(obj: unknown, key: K): obj is Record<K, unknown> {
  return typeof obj === "object" && obj !== null && key in obj;
}

function isToolStartEvent(obj: unknown): obj is SSEToolStartEvent {
  return has(obj, "tool_name") && typeof obj.tool_name === "string" && has(obj, "input");
}

function isToolEndEvent(obj: unknown): obj is SSEToolEndEvent {
  return has(obj, "tool_name") && typeof obj.tool_name === "string" && has(obj, "duration_ms");
}

function isTextDeltaEvent(obj: unknown): obj is SSETextDeltaEvent {
  return has(obj, "delta") && typeof obj.delta === "string";
}

function isDoneEvent(obj: unknown): obj is SSEDoneEvent {
  return has(obj, "answer") && typeof obj.answer === "string";
}

function isPersistEvent(obj: unknown): obj is SSEPersistEvent {
  return has(obj, "message_id") && has(obj, "persisted");
}

function isTitleUpdateEvent(obj: unknown): obj is SSETitleUpdateEvent {
  return has(obj, "title") && typeof obj.title === "string";
}

function isErrorEvent(obj: unknown): obj is SSEErrorEvent {
  return has(obj, "error") && typeof obj.error === "string";
}

function isDataBlockEvent(obj: unknown): obj is SSEDataBlockEvent {
  return has(obj, "query") && has(obj, "result");
}

// --- Streaming ---

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

  await checkAuth(res);
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

      switch (eventType) {
        case "tool_start":
          if (isToolStartEvent(data)) callbacks.onToolStart?.(data);
          break;
        case "tool_end":
          if (isToolEndEvent(data)) callbacks.onToolEnd?.(data);
          break;
        case "data_block":
          if (isDataBlockEvent(data)) callbacks.onDataBlock?.(data);
          break;
        case "text_delta":
          if (isTextDeltaEvent(data)) callbacks.onTextDelta?.(data);
          break;
        case "done":
          if (isDoneEvent(data)) callbacks.onDone?.(data);
          break;
        case "persist":
          if (isPersistEvent(data)) callbacks.onPersist?.(data);
          break;
        case "title_update":
          if (isTitleUpdateEvent(data)) callbacks.onTitleUpdate?.(data);
          break;
        case "error":
          if (isErrorEvent(data)) callbacks.onError?.(data);
          break;
      }
    }
  }
}
