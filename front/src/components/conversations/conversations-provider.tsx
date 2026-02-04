import { createContext, useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { createConversation, listConversations, removeConversation } from "@/lib/api";
import type { Conversation } from "@/types";

interface ConversationsContextValue {
  conversations: Conversation[];
  loading: boolean;
  refresh: () => void;
  updateTitle: (id: string, title: string) => void;
  create: (instrument: string) => Promise<Conversation>;
  remove: (id: string) => Promise<void>;
}

export const ConversationsContext = createContext<ConversationsContextValue | null>(null);

export function ConversationsProvider() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    listConversations(token)
      .then((data) => { if (!cancelled) setConversations(data); })
      .catch((err) => { if (!cancelled) console.error("Failed to load conversations:", err); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token]);

  const refresh = () => {
    if (!token) return;
    listConversations(token)
      .then(setConversations)
      .catch((err) => console.error("Failed to refresh conversations:", err));
  };

  const updateTitle = (id: string, title: string) => {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, title } : c)),
    );
  };

  const create = async (instrument: string) => {
    if (!token) throw new Error("Not authenticated");
    const conv = await createConversation(instrument, token);
    setConversations((prev) => [conv, ...prev]);
    return conv;
  };

  const remove = async (id: string) => {
    if (!token) throw new Error("Not authenticated");
    await removeConversation(id, token);
    setConversations((prev) => prev.filter((c) => c.id !== id));
  };

  return (
    <ConversationsContext.Provider value={{ conversations, loading, refresh, updateTitle, create, remove }}>
      <Outlet />
    </ConversationsContext.Provider>
  );
}
