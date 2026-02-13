import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { EllipsisIcon, PanelLeftIcon, Trash2Icon } from "lucide-react";
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

  const location = useLocation();
  const { dataPct, onDataResize } = usePanelLayout();
  const { sidebarOpen, toggleSidebar, closeSidebar } = useSidebar();
  const [selectedData, setSelectedData] = useState<DataBlock | null>(null);

  // Capture initial message from instrument page (sent via router state)
  const [initialMessage] = useState(() => {
    const msg = (location.state as { initialMessage?: string } | null)?.initialMessage ?? null;
    if (msg) window.history.replaceState({}, "", location.pathname);
    return msg;
  });

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
    if (window.innerWidth < 1024) closeSidebar();
  }, [id, closeSidebar]);

  const onConversationCreated = (convId: string) => {
    refresh();
    navigate(`/i/${symbol}/c/${convId}`, { replace: true });
  };

  // "new" is a sentinel — means user started typing on instrument page
  const conversationId = id === "new" ? undefined : id;

  const { messages, isLoading, error, send } = useChat({
    conversationId,
    token,
    instrument: symbol ?? "",
    onConversationCreated,
    onTitleUpdate: updateTitle,
  });

  // Auto-send initial message from instrument page
  const sentRef = useRef(false);

  useEffect(() => {
    if (initialMessage && !sentRef.current) {
      sentRef.current = true;
      send(initialMessage);
    }
  }, [initialMessage, send]);

  // Show preview until useChat has the real messages
  const displayMessages = messages.length === 0 && previewMessage ? [previewMessage] : messages;

  const handleSelectData = useCallback((data: DataBlock) => {
    setSelectedData((prev) => (prev === data ? null : data));
  }, []);

  const conversation = conversations.find((c) => c.id === id);
  const title = conversation?.title;

  const chatHeader = (
    <PanelHeader>
      <div className="flex items-center gap-1.5">
        {!sidebarOpen && (
          <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
            <PanelLeftIcon />
          </Button>
        )}
        {title && (
          <>
            <span className="min-w-0 flex-1 truncate text-sm font-medium">{title}</span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon-sm">
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
                      console.error("Failed to remove chat:", err instanceof Error ? err.message : err);
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
      error={error}
      send={send}
      selectedData={selectedData}
      onSelectData={handleSelectData}
      dataPct={dataPct}
      onDataResize={onDataResize}
      onCloseData={() => setSelectedData(null)}
    />
  );
}
