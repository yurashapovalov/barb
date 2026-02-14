import { useEffect, useState } from "react";
import { toast } from "sonner";
import { getOHLC, type OHLCBar } from "@/lib/api";
import { readCache, writeCache } from "@/lib/cache";

function cacheKey(symbol: string) {
  return `ohlc:${symbol}`;
}

export function useOHLC(symbol: string | undefined) {
  const [data, setData] = useState<OHLCBar[] | null>(
    () => symbol ? readCache<OHLCBar[]>(cacheKey(symbol)) : null,
  );
  const [loading, setLoading] = useState(
    () => !symbol || readCache(cacheKey(symbol)) === null,
  );

  useEffect(() => {
    if (!symbol) return;

    // On symbol change: show cached data immediately, or null
    const cached = readCache<OHLCBar[]>(cacheKey(symbol));
    setData(cached);
    setLoading(cached === null);

    let cancelled = false;
    getOHLC(symbol)
      .then((result) => {
        if (!cancelled) {
          setData(result);
          writeCache(cacheKey(symbol), result);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          toast.error(err instanceof Error ? err.message : "Failed to load chart data");
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [symbol]);

  return { data, loading };
}
