import { ChevronsLeftIcon, MessageCircleIcon, PlusIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { listConversations } from "@/lib/api";
import type { Conversation } from "@/types";
import { PanelHeader } from "./panel-header";

interface SidebarPanelProps {
  onCollapse?: () => void;
}

export function SidebarPanel({ onCollapse }: SidebarPanelProps) {
  const { user, session } = useAuth();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const email = user?.email ?? "user@example.com";
  const avatar = user?.user_metadata?.avatar_url as string | undefined;
  const token = session?.access_token ?? "";

  const [conversations, setConversations] = useState<Conversation[]>([]);

  useEffect(() => {
    if (!token) return;
    listConversations(token).then(setConversations).catch(() => {});
  }, [token]);

  return (
    <div className="flex h-full flex-col bg-sidebar">
      <PanelHeader>
        <Button variant="ghost" size="xs">
          {avatar && (
            <img
              src={avatar}
              alt=""
              className="size-5 rounded-full"
            />
          )}
          {email}
        </Button>
        <Button variant="ghost" size="icon-xs" onClick={onCollapse}>
          <ChevronsLeftIcon />
        </Button>
      </PanelHeader>
      <div className="flex flex-1 flex-col gap-8 overflow-y-auto px-2">
        <div className="flex flex-col gap-1">
          <span className="px-2 text-xs text-muted-foreground">Chats</span>
          <Button
            variant="ghost"
            size="sm"
            className="justify-start"
            onClick={() => navigate("/")}
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
