import { createContext, useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { createConversation, listConversations } from "@/lib/api";
import type { Conversation } from "@/types";

interface ConversationsContextValue {
  conversations: Conversation[];
  loading: boolean;
  refresh: () => void;
  updateTitle: (id: string, title: string) => void;
  create: (instrument: string) => Promise<Conversation>;
}

export const ConversationsContext = createContext<ConversationsContextValue | null>(null);

export function ConversationsProvider() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    listConversations(token)
      .then(setConversations)
      .catch((err) => console.error("Failed to load conversations:", err))
      .finally(() => setLoading(false));
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

  return (
    <ConversationsContext.Provider value={{ conversations, loading, refresh, updateTitle, create }}>
      <Outlet />
    </ConversationsContext.Provider>
  );
}
