import { useCallback, useEffect, useState } from "react";

const LG_BREAKPOINT = 1024;

function isDesktop() {
  return window.innerWidth >= LG_BREAKPOINT;
}

export function useSidebar() {
  const [open, setOpen] = useState(isDesktop);

  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${LG_BREAKPOINT}px)`);
    const handler = (e: MediaQueryListEvent) => setOpen(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const toggle = useCallback(() => setOpen((v) => !v), []);
  const close = useCallback(() => setOpen(false), []);

  return { sidebarOpen: open, toggleSidebar: toggle, closeSidebar: close, isDesktop: isDesktop() };
}
