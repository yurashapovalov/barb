import type { ReactNode } from "react";
import { MessageCirclePlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Conversation } from "@/types";

interface InstrumentPanelProps {
  header: ReactNode;
  conversations: Conversation[];
  loading: boolean;
  onNewChat: () => void;
  onSelectChat: (conv: Conversation) => void;
}

export function InstrumentPanel({ header, conversations, loading, onNewChat, onSelectChat }: InstrumentPanelProps) {
  return (
    <div className="flex h-full flex-col bg-background">
      {header}
      <div className="p-4">
        <Button onClick={onNewChat}>
          <MessageCirclePlusIcon />
          New chat
        </Button>
        {loading ? (
          <div className="mt-4 text-sm text-muted-foreground">Loading...</div>
        ) : (
          <div className="mt-4 flex flex-col gap-2">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                className="rounded-lg border p-3 text-left hover:bg-accent"
                onClick={() => onSelectChat(conv)}
              >
                <div className="text-sm font-medium">{conv.title}</div>
                <div className="text-xs text-muted-foreground">
                  {new Date(conv.updated_at).toLocaleDateString()}
                </div>
              </button>
            ))}
            {conversations.length === 0 && (
              <div className="text-sm text-muted-foreground">
                No conversations yet. Start a new chat!
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
