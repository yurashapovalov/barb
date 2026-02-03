import { createContext, useCallback, useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { createConversation, listConversations } from "@/lib/api";
import type { Conversation } from "@/types";

interface ConversationsContextValue {
  conversations: Conversation[];
  refresh: () => void;
  create: (instrument: string) => Promise<Conversation>;
}

export const ConversationsContext = createContext<ConversationsContextValue | null>(null);

export function ConversationsProvider() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";

  const [conversations, setConversations] = useState<Conversation[]>([]);

  useEffect(() => {
    if (!token) return;
    listConversations(token).then(setConversations).catch(() => {});
  }, [token]);

  const refresh = useCallback(() => {
    if (!token) return;
    listConversations(token).then(setConversations).catch(() => {});
  }, [token]);

  const create = useCallback(async (instrument: string) => {
    const conv = await createConversation(instrument, token);
    setConversations((prev) => [conv, ...prev]);
    return conv;
  }, [token]);

  return (
    <ConversationsContext.Provider value={{ conversations, refresh, create }}>
      <Outlet />
    </ConversationsContext.Provider>
  );
}
