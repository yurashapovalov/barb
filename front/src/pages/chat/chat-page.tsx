import { SidebarPanel } from "@/components/panels/sidebar-panel";
import { ChatPanel } from "@/components/panels/chat-panel";
import { DataPanel } from "@/components/panels/data-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import { usePanelLayout } from "@/hooks/use-panel-layout";

export function ChatPage() {
  const { containerRef, sidebarWidth, dataPct, dataMinPx, onSidebarResize, onDataResize } = usePanelLayout();

  return (
    <div ref={containerRef} className="flex h-full">
      <div style={{ width: sidebarWidth }} className="hidden shrink-0 lg:block">
        <SidebarPanel />
      </div>
      <ResizeHandle className="hidden lg:block" onResize={onSidebarResize} />
      <div className="min-w-0 flex-1">
        <ChatPanel />
      </div>
      <ResizeHandle className="hidden lg:block" onResize={onDataResize} />
      <div style={{ width: `${dataPct}%`, minWidth: dataMinPx }} className="hidden shrink-0 lg:block">
        <DataPanel />
      </div>
    </div>
  );
}
