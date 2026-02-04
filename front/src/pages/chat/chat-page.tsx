import { useCallback, useEffect, useState } from "react";
import { SidebarPanel } from "@/components/panels/sidebar-panel";
import { ChatPanel } from "@/components/panels/chat-panel";
import { DataPanel } from "@/components/panels/data-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import { usePanelLayout } from "@/hooks/use-panel-layout";
import type { ChatState } from "@/hooks/use-chat";
import type { DataBlock } from "@/types";

interface ChatPageProps {
  conversationId?: string;
  messages: ChatState["messages"];
  isLoading: ChatState["isLoading"];
  error: ChatState["error"];
  send: ChatState["send"];
}

export function ChatPage({ conversationId, messages, isLoading, error, send }: ChatPageProps) {
  const { sidebarWidth, dataPct, onSidebarResize, onDataResize } = usePanelLayout();
  const [selectedData, setSelectedData] = useState<DataBlock | null>(null);

  useEffect(() => {
    setSelectedData(null);
  }, [conversationId]);

  const handleSelectData = useCallback((data: DataBlock) => {
    setSelectedData((prev) => (prev === data ? null : data));
  }, []);

  return (
    <div className="flex h-full">
      <div style={{ width: sidebarWidth }} className="hidden shrink-0 lg:block">
        <SidebarPanel />
      </div>
      <ResizeHandle className="hidden lg:block" onResize={onSidebarResize} />
      <div className="min-w-0 flex-1">
        <ChatPanel messages={messages} isLoading={isLoading} error={error} send={send} selectedData={selectedData} onSelectData={handleSelectData} />
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
