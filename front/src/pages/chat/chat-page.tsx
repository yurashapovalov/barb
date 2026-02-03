import { SidebarPanel } from "@/components/panels/sidebar-panel";
import { ChatPanel } from "@/components/panels/chat-panel";
import { DataPanel } from "@/components/panels/data-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import { usePanelLayout } from "@/hooks/use-panel-layout";
import type { ChatState } from "@/hooks/use-chat";

interface ChatPageProps {
  messages: ChatState["messages"];
  isLoading: ChatState["isLoading"];
  error: ChatState["error"];
  send: ChatState["send"];
}

export function ChatPage({ messages, isLoading, error, send }: ChatPageProps) {
  const { sidebarWidth, dataPct, dataMinPx, onSidebarResize, onDataResize } = usePanelLayout();

  return (
    <div className="flex h-full">
      <div style={{ width: sidebarWidth }} className="hidden shrink-0 lg:block">
        <SidebarPanel />
      </div>
      <ResizeHandle className="hidden lg:block" onResize={onSidebarResize} />
      <div className="min-w-0 flex-1">
        <ChatPanel messages={messages} isLoading={isLoading} error={error} send={send} />
      </div>
      <ResizeHandle className="hidden lg:block" onResize={onDataResize} />
      <div style={{ width: `${dataPct}vw`, minWidth: dataMinPx }} className="hidden shrink-0 lg:block">
        <DataPanel />
      </div>
    </div>
  );
}
