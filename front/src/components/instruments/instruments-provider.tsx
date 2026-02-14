import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import { addUserInstrument, listUserInstruments, removeUserInstrument } from "@/lib/api";
import { readCache, writeCache } from "@/lib/cache";
import type { Instrument, UserInstrument } from "@/types";
import { InstrumentsContext } from "./instruments-context";

function cacheKey(userId: string) {
  return `instruments:${userId}`;
}

export function InstrumentsProvider() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";
  const userId = session?.user?.id ?? "";

  const [instruments, setInstruments] = useState<UserInstrument[]>(
    () => (userId ? readCache<UserInstrument[]>(cacheKey(userId)) : null) ?? [],
  );
  const [loading, setLoading] = useState(
    () => !userId || readCache(cacheKey(userId)) === null,
  );
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!token || !userId) return;
    let cancelled = false;
    setError(null);
    listUserInstruments(token)
      .then((data) => {
        if (!cancelled) {
          setInstruments(data);
          writeCache(cacheKey(userId), data);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Failed to load instruments";
          setError(msg);
          toast.error(msg);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  };

  useEffect(load, [token, userId]);

  const retry = () => {
    setError(null);
    setLoading(true);
    load();
  };

  const add = async (inst: Instrument) => {
    if (!token) throw new Error("Not authenticated");
    await addUserInstrument(inst.symbol, token);
    setInstruments((prev) => {
      if (prev.some((i) => i.instrument === inst.symbol)) return prev;
      const next = [...prev, {
        instrument: inst.symbol,
        name: inst.name,
        exchange: inst.exchange,
        image_url: inst.image_url,
        added_at: new Date().toISOString(),
      }];
      writeCache(cacheKey(userId), next);
      return next;
    });
  };

  const remove = async (symbol: string) => {
    if (!token) throw new Error("Not authenticated");
    await removeUserInstrument(symbol, token);
    setInstruments((prev) => {
      const next = prev.filter((i) => i.instrument !== symbol);
      writeCache(cacheKey(userId), next);
      return next;
    });
  };

  return (
    <InstrumentsContext.Provider value={{ instruments, loading, error, add, remove, retry }}>
      <Outlet />
    </InstrumentsContext.Provider>
  );
}
