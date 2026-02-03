import { useRef, useState } from "react";

const SIDEBAR_DEFAULT = 240;
const SIDEBAR_MIN = 240;
const SIDEBAR_MAX = 320;

const DATA_DEFAULT_PCT = 35;
const DATA_MIN_PX = 480;
const DATA_MAX_PCT = 60;

const STORAGE_KEY_SIDEBAR = "panel-sidebar-width";
const STORAGE_KEY_DATA = "panel-data-pct";

function loadNumber(key: string, fallback: number): number {
  const raw = localStorage.getItem(key);
  if (raw === null) return fallback;
  const n = Number(raw);
  return Number.isFinite(n) ? n : fallback;
}

export function usePanelLayout() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [sidebarWidth, setSidebarWidth] = useState(() => loadNumber(STORAGE_KEY_SIDEBAR, SIDEBAR_DEFAULT));
  const [dataPct, setDataPct] = useState(() => loadNumber(STORAGE_KEY_DATA, DATA_DEFAULT_PCT));

  const onSidebarResize = (delta: number) => {
    setSidebarWidth((w) => {
      const next = Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, w + delta));
      localStorage.setItem(STORAGE_KEY_SIDEBAR, String(next));
      return next;
    });
  };

  const onDataResize = (delta: number) => {
    const container = containerRef.current;
    if (!container) return;
    const pctDelta = (delta / container.offsetWidth) * 100;
    const minPct = (DATA_MIN_PX / container.offsetWidth) * 100;
    setDataPct((w) => {
      const next = Math.min(DATA_MAX_PCT, Math.max(minPct, w - pctDelta));
      localStorage.setItem(STORAGE_KEY_DATA, String(next));
      return next;
    });
  };

  return { containerRef, sidebarWidth, dataPct, dataMinPx: DATA_MIN_PX, onSidebarResize, onDataResize };
}
