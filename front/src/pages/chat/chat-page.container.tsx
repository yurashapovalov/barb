import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { EllipsisIcon, PanelLeftIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import { useChat } from "@/hooks/use-chat";
import { useConversations } from "@/hooks/use-conversations";
import { usePanelLayout } from "@/hooks/use-panel-layout";
import { useSidebar } from "@/hooks/use-sidebar";
import { PanelHeader } from "@/components/panels/panel-header";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { DataBlock, Message } from "@/types";
import { ChatPage } from "./chat-page";

export function ChatPageContainer() {
  const { symbol, id } = useParams<{ symbol: string; id: string }>();
  const { session } = useAuth();
  const { conversations, refresh, updateTitle, remove } = useConversations();
  const navigate = useNavigate();
  const token = session?.access_token ?? "";

  const { dataPct, onDataResize } = usePanelLayout();
  const { sidebarOpen, toggleSidebar } = useSidebar();
  const [selectedData, setSelectedData] = useState<DataBlock | null>(null);

  // Read initial message from sessionStorage (survives StrictMode remount)
  const initialMessage = id === "new" ? sessionStorage.getItem("barb:initial-msg") : null;

  // Pre-render user message so it's visible from the first frame
  const [previewMessage] = useState<Message | null>(() => {
    if (!initialMessage) return null;
    return {
      id: crypto.randomUUID(),
      conversation_id: "pending",
      role: "user" as const,
      content: initialMessage,
      data: null,
      usage: null,
      created_at: new Date().toISOString(),
    };
  });

  useEffect(() => {
    setSelectedData(null);
  }, [id]);

  const onConversationCreated = (convId: string) => {
    refresh();
    navigate(`/i/${symbol}/c/${convId}`, { replace: true });
  };

  // "new" is a sentinel — means user started typing on instrument page
  const conversationId = id === "new" ? undefined : id;

  const { messages, isLoading, error, send, pendingTool, confirmBacktest } = useChat({
    conversationId,
    token,
    instrument: symbol ?? "",
    onConversationCreated,
    onTitleUpdate: updateTitle,
  });

  // Auto-send initial message from instrument page
  const sentRef = useRef(false);
  const sendRef = useRef(send);
  sendRef.current = send;

  useEffect(() => {
    if (initialMessage && !sentRef.current) {
      sentRef.current = true;
      sessionStorage.removeItem("barb:initial-msg");
      sendRef.current(initialMessage);
    }
  }, [initialMessage]);

  // Show preview until useChat has the real messages (not on error — send failed)
  const displayMessages = messages.length === 0 && previewMessage && !error ? [previewMessage] : messages;

  const handleSelectData = useCallback((data: DataBlock) => {
    setSelectedData((prev) => (prev === data ? null : data));
  }, []);

  const conversation = conversations.find((c) => c.id === id);
  const title = conversation?.title;

  const chatHeader = (
    <PanelHeader>
      <div className="flex items-center gap-1.5">
        {!sidebarOpen && (
          <Button variant="ghost" size="icon-sm" onClick={toggleSidebar} aria-label="Open sidebar">
            <PanelLeftIcon />
          </Button>
        )}
        {title && (
          <>
            <span className="min-w-0 flex-1 truncate text-sm font-medium">{title}</span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon-sm" aria-label="Chat options">
                  <EllipsisIcon />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuItem
                  onClick={async () => {
                    if (!id) return;
                    try {
                      await remove(id);
                      navigate(`/i/${symbol}`, { replace: true });
                    } catch (err) {
                      toast.error(err instanceof Error ? err.message : "Failed to remove chat");
                    }
                  }}
                >
                  <Trash2Icon />
                  Remove chat
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        )}
      </div>
    </PanelHeader>
  );

  return (
    <ChatPage
      chatHeader={chatHeader}
      messages={displayMessages}
      isLoading={isLoading}
      send={send}
      selectedData={selectedData}
      onSelectData={handleSelectData}
      dataPct={dataPct}
      onDataResize={onDataResize}
      onCloseData={() => setSelectedData(null)}
      pendingTool={pendingTool}
      confirmBacktest={confirmBacktest}
    />
  );
}
