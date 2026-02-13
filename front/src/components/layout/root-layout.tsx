import { Outlet } from "react-router-dom";
import { SidebarPanel } from "@/components/panels/sidebar-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import { usePanelLayout } from "@/hooks/use-panel-layout";
import { useSidebar } from "@/hooks/use-sidebar";

export function RootLayout() {
  const { sidebarOpen, toggleSidebar } = useSidebar();
  const { sidebarWidth, onSidebarResize } = usePanelLayout();

  return (
    <div className="flex h-dvh overflow-hidden">
      {sidebarOpen && (
        <>
          <div
            style={{ "--sidebar-w": `${sidebarWidth}px` } as React.CSSProperties}
            className="w-[80vw] shrink-0 lg:w-(--sidebar-w)"
          >
            <SidebarPanel onCollapse={toggleSidebar} />
          </div>
          <ResizeHandle className="hidden lg:block" onResize={onSidebarResize} />
        </>
      )}
      <main className="min-w-full flex-1 lg:min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
