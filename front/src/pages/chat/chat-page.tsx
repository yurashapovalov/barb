import type { ReactNode } from "react";
import { ChatPanel } from "@/components/panels/chat-panel";
import { DataPanel } from "@/components/panels/data-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import type { ChatState } from "@/hooks/use-chat";
import type { DataBlock } from "@/types";

interface ChatPageProps {
  chatHeader: ReactNode;
  messages: ChatState["messages"];
  isLoading: ChatState["isLoading"];
  send: ChatState["send"];
  selectedData: DataBlock | null;
  onSelectData: (data: DataBlock) => void;
  dataPct: number;
  onDataResize: (delta: number) => void;
  onCloseData: () => void;
}

export function ChatPage({
  chatHeader,
  messages,
  isLoading,
  send,
  selectedData,
  onSelectData,
  dataPct,
  onDataResize,
  onCloseData,
}: ChatPageProps) {
  return (
    <div className="flex h-full">
      <div className="min-w-full flex-1 lg:min-w-0">
        <ChatPanel header={chatHeader} messages={messages} isLoading={isLoading} send={send} selectedData={selectedData} onSelectData={onSelectData} />
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
