import { PanelLeftIcon } from "lucide-react";
import { SidebarPanel } from "@/components/panels/sidebar-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import { PanelHeader } from "@/components/panels/panel-header";
import { Button } from "@/components/ui/button";
import { usePanelLayout } from "@/hooks/use-panel-layout";
import { useSidebar } from "@/hooks/use-sidebar";

export function HomePage() {
  const { sidebarWidth, onSidebarResize } = usePanelLayout();
  const { sidebarOpen, toggleSidebar } = useSidebar();

  return (
    <div className="flex h-full">
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
      <div className="min-w-full flex-1 lg:min-w-0">
        <PanelHeader>
          {!sidebarOpen && (
            <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
              <PanelLeftIcon />
            </Button>
          )}
        </PanelHeader>
        <div className="flex h-full items-center justify-center">
          <p className="text-sm text-muted-foreground">Select a symbol to get started</p>
        </div>
      </div>
    </div>
  );
}
