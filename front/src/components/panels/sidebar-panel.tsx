import { ChevronsLeftIcon, MessageCircleIcon, PlusIcon } from "lucide-react";
import { useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useConversations } from "@/hooks/use-conversations";
import { PanelHeader } from "./panel-header";

interface SidebarPanelProps {
  onCollapse?: () => void;
}

export function SidebarPanel({ onCollapse }: SidebarPanelProps) {
  const { user } = useAuth();
  const { conversations, create } = useConversations();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const displayName = user?.user_metadata?.full_name ?? user?.email ?? "User";
  const avatar = user?.user_metadata?.avatar_url as string | undefined;

  const handleNewChat = useCallback(async () => {
    try {
      const conv = await create("NQ");
      navigate(`/c/${conv.id}`);
    } catch {}
  }, [create, navigate]);

  return (
    <div className="flex h-full flex-col bg-sidebar">
      <PanelHeader>
        <Button variant="ghost" size="sm">
          {avatar && (
            <img
              src={avatar}
              alt=""
              className="size-5 rounded-full"
            />
          )}
          {displayName}
        </Button>
        <Button variant="ghost" size="icon-sm" onClick={onCollapse}>
          <ChevronsLeftIcon />
        </Button>
      </PanelHeader>
      <div className="flex flex-1 flex-col overflow-y-auto px-2">
        <div className="mt-12 flex flex-col gap-1">
          <span className="px-2 text-xs text-muted-foreground">Chats</span>
          <Button
            variant="ghost"
            size="sm"
            className="justify-start"
            onClick={handleNewChat}
          >
            <PlusIcon />
            New chat
          </Button>
          {conversations.map((conv) => (
            <Button
              key={conv.id}
              variant="ghost"
              size="sm"
              className={`justify-start ${conv.id === id ? "bg-accent" : ""}`}
              onClick={() => navigate(`/c/${conv.id}`)}
            >
              <MessageCircleIcon />
              <span className="truncate">{conv.title}</span>
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
