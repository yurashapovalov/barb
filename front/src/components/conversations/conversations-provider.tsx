import { useEffect, useRef, useState } from "react";
import { Outlet, useParams } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { createConversation, listConversations, removeConversation } from "@/lib/api";
import { readCache, removeCache, writeCache } from "@/lib/cache";
import type { Conversation } from "@/types";
import { ConversationsContext } from "./conversations-context";

function cacheKey(symbol: string) {
  return `conversations:${symbol}`;
}

export function ConversationsProvider() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";
  const userId = session?.user?.id ?? "";
  const { symbol } = useParams<{ symbol: string }>();

  // Refs so callbacks always see the latest values
  const symbolRef = useRef(symbol);
  symbolRef.current = symbol;
  const userIdRef = useRef(userId);
  userIdRef.current = userId;

  const [conversations, setConversations] = useState<Conversation[]>(
    () => (symbol ? readCache<Conversation[]>(cacheKey(symbol)) : null) ?? [],
  );
  const [loading, setLoading] = useState(
    () => !symbol || readCache(cacheKey(symbol)) === null,
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

  const writeConversationsCache = (next: Conversation[]) => {
    if (symbolRef.current) writeCache(cacheKey(symbolRef.current), next);
    if (userIdRef.current) removeCache(`chats:${userIdRef.current}`);
  };

  const refresh = () => {
    if (!token || !symbolRef.current) return;
    listConversations(token, symbolRef.current)
      .then((data) => {
        setConversations(data);
        writeConversationsCache(data);
      })
      .catch((err) => console.error("Failed to refresh conversations:", err));
  };

  const updateTitle = (id: string, title: string) => {
    setConversations((prev) => {
      const next = prev.map((c) => (c.id === id ? { ...c, title } : c));
      writeConversationsCache(next);
      return next;
    });
  };

  const create = async (instrument: string) => {
    if (!token) throw new Error("Not authenticated");
    const conv = await createConversation(instrument, token);
    setConversations((prev) => {
      const next = [conv, ...prev];
      writeConversationsCache(next);
      return next;
    });
    return conv;
  };

  const remove = async (id: string) => {
    if (!token) throw new Error("Not authenticated");
    await removeConversation(id, token);
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      writeConversationsCache(next);
      return next;
    });
  };

  return (
    <ConversationsContext.Provider value={{ conversations, loading, refresh, updateTitle, create, remove }}>
      <Outlet />
    </ConversationsContext.Provider>
  );
}
