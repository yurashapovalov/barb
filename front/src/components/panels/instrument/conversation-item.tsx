import { EllipsisIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatRelativeDate } from "@/lib/date";
import type { Conversation } from "@/types";

export function ConversationItem({
  conversation,
  onSelect,
  onRemove,
}: {
  conversation: Conversation;
  onSelect: () => void;
  onRemove: () => Promise<void>;
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg p-3 hover:bg-accent">
      <button className="min-w-0 flex-1 cursor-pointer text-left" onClick={onSelect}>
        <div className="truncate text-base tracking-tight">{conversation.title}</div>
      </button>
      <div className="flex items-center gap-1">
        <span className="text-sm text-muted-foreground">
          {formatRelativeDate(conversation.updated_at)}
        </span>
        <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon-sm" aria-label="Chat options">
            <EllipsisIcon />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={async () => {
              try {
                await onRemove();
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
      </div>
    </div>
  );
}
