import type { ChatResponse } from "@/types";

const API_URL = import.meta.env.VITE_API_URL as string;

interface HistoryEntry {
  role: "user" | "model";
  content: string;
}

export async function sendMessage(
  message: string,
  history: HistoryEntry[],
  instrument: string,
  token: string,
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, history, instrument }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return res.json();
}
