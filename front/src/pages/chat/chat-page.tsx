import type { ReactNode } from "react";
import { SidebarPanel } from "@/components/panels/sidebar-panel";
import { ChatPanel } from "@/components/panels/chat-panel";
import { DataPanel } from "@/components/panels/data-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import type { ChatState } from "@/hooks/use-chat";
import type { DataBlock } from "@/types";

interface ChatPageProps {
  sidebarOpen: boolean;
  sidebarWidth: number;
  onSidebarResize: (delta: number) => void;
  onToggleSidebar: () => void;
  chatHeader: ReactNode;
  messages: ChatState["messages"];
  isLoading: ChatState["isLoading"];
  error: ChatState["error"];
  send: ChatState["send"];
  selectedData: DataBlock | null;
  onSelectData: (data: DataBlock) => void;
  dataPct: number;
  onDataResize: (delta: number) => void;
  onCloseData: () => void;
}

export function ChatPage({
  sidebarOpen,
  sidebarWidth,
  onSidebarResize,
  onToggleSidebar,
  chatHeader,
  messages,
  isLoading,
  error,
  send,
  selectedData,
  onSelectData,
  dataPct,
  onDataResize,
  onCloseData,
}: ChatPageProps) {
  return (
    <div className="flex h-full">
      {sidebarOpen && (
        <>
          <div
            style={{ "--sidebar-w": `${sidebarWidth}px` } as React.CSSProperties}
            className="w-[80vw] shrink-0 lg:w-(--sidebar-w)"
          >
            <SidebarPanel onCollapse={onToggleSidebar} />
          </div>
          <ResizeHandle className="hidden lg:block" onResize={onSidebarResize} />
        </>
      )}
      <div className="min-w-full flex-1 lg:min-w-0">
        <ChatPanel header={chatHeader} messages={messages} isLoading={isLoading} error={error} send={send} selectedData={selectedData} onSelectData={onSelectData} />
      </div>
      {selectedData && (
        <>
          <ResizeHandle className="hidden lg:block" onResize={onDataResize} />
          <div
            className="fixed inset-0 z-50 lg:relative lg:inset-auto lg:z-auto lg:w-(--data-w)"
            style={{ "--data-w": `${dataPct}vw` } as React.CSSProperties}
          >
            <DataPanel data={selectedData} onClose={onCloseData} />
          </div>
        </>
      )}
    </div>
  );
}
