import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
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
import type { DataBlock } from "@/types";
import { ChatPage } from "./chat-page";

export function ChatPageContainer() {
  const { id } = useParams<{ id: string }>();
  const { session } = useAuth();
  const { conversations, loading, updateTitle, remove } = useConversations();
  const navigate = useNavigate();
  const token = session?.access_token ?? "";

  const { sidebarWidth, dataPct, onSidebarResize, onDataResize } = usePanelLayout();
  const { sidebarOpen, toggleSidebar, closeSidebar } = useSidebar();
  const [selectedData, setSelectedData] = useState<DataBlock | null>(null);

  // Redirect to most recent conversation on bare "/"
  useEffect(() => {
    if (!loading && !id && conversations.length > 0) {
      navigate(`/c/${conversations[0].id}`, { replace: true });
    }
  }, [loading, id, conversations, navigate]);

  useEffect(() => {
    setSelectedData(null);
    closeSidebar();
  }, [id, closeSidebar]);

  const onConversationCreated = (convId: string) =>
    navigate(`/c/${convId}`, { replace: true });

  const { messages, isLoading, error, send } = useChat({
    conversationId: id,
    token,
    onConversationCreated,
    onTitleUpdate: updateTitle,
  });

  const handleSelectData = useCallback((data: DataBlock) => {
    setSelectedData((prev) => (prev === data ? null : data));
  }, []);

  if (loading) return null;

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
                <DropdownMenuItem onClick={() => { if (id) remove(id).then(() => navigate("/", { replace: true })); }}>
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
      sidebarOpen={sidebarOpen}
      sidebarWidth={sidebarWidth}
      onSidebarResize={onSidebarResize}
      onToggleSidebar={toggleSidebar}
      chatHeader={chatHeader}
      messages={messages}
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
