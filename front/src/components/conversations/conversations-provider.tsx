import { useEffect, useState } from "react";
import { Outlet, useParams } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { createConversation, listConversations, removeConversation } from "@/lib/api";
import { readCache, writeCache } from "@/lib/cache";
import type { Conversation } from "@/types";
import { ConversationsContext } from "./conversations-context";

function cacheKey(symbol: string) {
  return `conversations:${symbol}`;
}

export function ConversationsProvider() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";
  const { symbol } = useParams<{ symbol: string }>();

  const [conversations, setConversations] = useState<Conversation[]>(
    () => (symbol ? readCache<Conversation[]>(cacheKey(symbol)) : null) ?? [],
  );
  const [loading, setLoading] = useState(
    () => symbol ? readCache(cacheKey(symbol)) === null : true,
  );

  useEffect(() => {
    if (!token || !symbol) return;
    let cancelled = false;
    listConversations(token, symbol)
      .then((data) => {
        if (!cancelled) {
          setConversations(data);
          writeCache(cacheKey(symbol), data);
        }
      })
      .catch((err) => { if (!cancelled) console.error("Failed to load conversations:", err); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token, symbol]);

  const refresh = () => {
    if (!token || !symbol) return;
    listConversations(token, symbol)
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
    setConversations((prev) => {
      const next = [conv, ...prev];
      if (symbol) writeCache(cacheKey(symbol), next);
      return next;
    });
    return conv;
  };

  const remove = async (id: string) => {
    if (!token) throw new Error("Not authenticated");
    await removeConversation(id, token);
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (symbol) writeCache(cacheKey(symbol), next);
      return next;
    });
  };

  return (
    <ConversationsContext.Provider value={{ conversations, loading, refresh, updateTitle, create, remove }}>
      <Outlet />
    </ConversationsContext.Provider>
  );
}
