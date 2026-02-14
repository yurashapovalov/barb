import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import { createConversation, listConversations, removeConversation } from "@/lib/api";
import { readCache, writeCache } from "@/lib/cache";
import type { Conversation } from "@/types";
import { ConversationsContext } from "./conversations-context";

function cacheKey(userId: string) {
  return `conversations:${userId}`;
}

export function ConversationsProvider() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";
  const userId = session?.user?.id ?? "";

  const [conversations, setConversations] = useState<Conversation[]>(
    () => (userId ? readCache<Conversation[]>(cacheKey(userId)) : null) ?? [],
  );
  const [loading, setLoading] = useState(
    () => !userId || readCache(cacheKey(userId)) === null,
  );
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!token || !userId) return;
    let cancelled = false;
    setError(null);
    listConversations(token)
      .then((data) => {
        if (!cancelled) {
          setConversations(data);
          writeCache(cacheKey(userId), data);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Failed to load conversations";
          setError(msg);
          toast.error(msg);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  };

  useEffect(load, [token, userId]);

  const updateCache = (next: Conversation[]) => {
    if (userId) writeCache(cacheKey(userId), next);
  };

  const refresh = () => {
    if (!token) return;
    setError(null);
    listConversations(token)
      .then((data) => {
        setConversations(data);
        updateCache(data);
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : "Failed to refresh conversations";
        setError(msg);
        toast.error(msg);
      });
  };

  const retry = () => {
    setError(null);
    setLoading(true);
    load();
  };

  const updateTitle = (id: string, title: string) => {
    setConversations((prev) => {
      const next = prev.map((c) => (c.id === id ? { ...c, title } : c));
      updateCache(next);
      return next;
    });
  };

  const create = async (instrument: string) => {
    if (!token) throw new Error("Not authenticated");
    const conv = await createConversation(instrument, token);
    setConversations((prev) => {
      const next = [conv, ...prev];
      updateCache(next);
      return next;
    });
    return conv;
  };

  const remove = async (id: string) => {
    if (!token) throw new Error("Not authenticated");
    await removeConversation(id, token);
    setConversations((prev) => {
      const next = prev.filter((c) => c.id !== id);
      updateCache(next);
      return next;
    });
  };

  return (
    <ConversationsContext.Provider value={{ conversations, loading, error, refresh, retry, updateTitle, create, remove }}>
      <Outlet />
    </ConversationsContext.Provider>
  );
}
