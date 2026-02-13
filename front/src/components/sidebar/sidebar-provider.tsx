import { useCallback, useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { SidebarContext } from "./sidebar-context";

const LG_BREAKPOINT = 1024;

export function SidebarProvider() {
  const [open, setOpen] = useState(() => window.innerWidth >= LG_BREAKPOINT);

  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${LG_BREAKPOINT}px)`);
    const handler = (e: MediaQueryListEvent) => setOpen(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const toggle = useCallback(() => setOpen((v) => !v), []);
  const close = useCallback(() => setOpen(false), []);

  return (
    <SidebarContext.Provider value={{ sidebarOpen: open, toggleSidebar: toggle, closeSidebar: close }}>
      <Outlet />
    </SidebarContext.Provider>
  );
}
