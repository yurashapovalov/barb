import type { ChatResponse, Conversation } from "@/types";

const API_URL = import.meta.env.VITE_API_URL as string;

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

export async function sendMessage(
  conversationId: string,
  message: string,
  token: string,
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ conversation_id: conversationId, message }),
  });
  return handleResponse<ChatResponse>(res);
}
