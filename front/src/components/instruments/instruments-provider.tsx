import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
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
    () => readCache<UserInstrument[]>(cacheKey(userId)) ?? [],
  );
  const [loading, setLoading] = useState(() => readCache(cacheKey(userId)) === null);

  useEffect(() => {
    if (!token || !userId) return;
    let cancelled = false;
    listUserInstruments(token)
      .then((data) => {
        if (!cancelled) {
          setInstruments(data);
          writeCache(cacheKey(userId), data);
        }
      })
      .catch((err) => { if (!cancelled) console.error("Failed to load instruments:", err); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token, userId]);

  const add = async (inst: Instrument) => {
    if (!token) throw new Error("Not authenticated");
    await addUserInstrument(inst.symbol, token);
    setInstruments((prev) => {
      const next = [...prev, {
        instrument: inst.symbol,
        name: inst.name,
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
    <InstrumentsContext.Provider value={{ instruments, loading, add, remove }}>
      <Outlet />
    </InstrumentsContext.Provider>
  );
}
