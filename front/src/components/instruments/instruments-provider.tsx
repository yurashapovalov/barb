import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { addUserInstrument, listUserInstruments, removeUserInstrument } from "@/lib/api";
import type { UserInstrument } from "@/types";
import { InstrumentsContext } from "./instruments-context";

export function InstrumentsProvider() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";

  const [instruments, setInstruments] = useState<UserInstrument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    listUserInstruments(token)
      .then((data) => { if (!cancelled) setInstruments(data); })
      .catch((err) => { if (!cancelled) console.error("Failed to load instruments:", err); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token]);

  const add = async (symbol: string) => {
    if (!token) throw new Error("Not authenticated");
    await addUserInstrument(symbol, token);
    setInstruments((prev) => [...prev, { instrument: symbol, added_at: new Date().toISOString() }]);
  };

  const remove = async (symbol: string) => {
    if (!token) throw new Error("Not authenticated");
    await removeUserInstrument(symbol, token);
    setInstruments((prev) => prev.filter((i) => i.instrument !== symbol));
  };

  return (
    <InstrumentsContext.Provider value={{ instruments, loading, add, remove }}>
      <Outlet />
    </InstrumentsContext.Provider>
  );
}
