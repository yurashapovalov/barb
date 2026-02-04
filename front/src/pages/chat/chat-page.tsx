import { useCallback, useEffect, useState } from "react";
import { SidebarPanel } from "@/components/panels/sidebar-panel";
import { ChatPanel } from "@/components/panels/chat-panel";
import { DataPanel } from "@/components/panels/data-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import { usePanelLayout } from "@/hooks/use-panel-layout";
import { useSidebar } from "@/hooks/use-sidebar";
import type { ChatState } from "@/hooks/use-chat";
import type { DataBlock } from "@/types";

interface ChatPageProps {
  conversationId?: string;
  title?: string;
  messages: ChatState["messages"];
  isLoading: ChatState["isLoading"];
  error: ChatState["error"];
  send: ChatState["send"];
}

export function ChatPage({ conversationId, title, messages, isLoading, error, send }: ChatPageProps) {
  const { sidebarWidth, dataPct, onSidebarResize, onDataResize } = usePanelLayout();
  const { sidebarOpen, toggleSidebar, closeSidebar } = useSidebar();
  const [selectedData, setSelectedData] = useState<DataBlock | null>(null);

  useEffect(() => {
    setSelectedData(null);
    closeSidebar();
  }, [conversationId, closeSidebar]);

  const handleSelectData = useCallback((data: DataBlock) => {
    setSelectedData((prev) => (prev === data ? null : data));
  }, []);

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
        <ChatPanel title={title} sidebarOpen={sidebarOpen} onToggleSidebar={toggleSidebar} messages={messages} isLoading={isLoading} error={error} send={send} selectedData={selectedData} onSelectData={handleSelectData} />
      </div>
      {selectedData && (
        <>
          <ResizeHandle className="hidden lg:block" onResize={onDataResize} />
          <div
            className="fixed inset-0 z-50 lg:relative lg:inset-auto lg:z-auto lg:w-(--data-w)"
            style={{ "--data-w": `${dataPct}vw` } as React.CSSProperties}
          >
            <DataPanel data={selectedData} onClose={() => setSelectedData(null)} />
          </div>
        </>
      )}
    </div>
  );
}
