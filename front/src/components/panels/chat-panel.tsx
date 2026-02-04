import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai/conversation";
import { DataCard } from "@/components/ai/data-card";
import { Message, MessageAction, MessageActions, MessageContent, MessageResponse } from "@/components/ai/message";
import { EllipsisIcon, MessageCircleIcon, PanelLeftIcon, ThumbsDownIcon, ThumbsUpIcon, Trash2Icon } from "lucide-react";
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputProvider,
  PromptInputSubmit,
  usePromptInputController,
} from "@/components/ai/prompt-input";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ChatState } from "@/hooks/use-chat";
import { parseContent } from "@/lib/parse-content";
import type { DataBlock } from "@/types";
import { PanelHeader } from "./panel-header";

interface ChatPanelProps {
  title?: string;
  sidebarOpen?: boolean;
  onToggleSidebar?: () => void;
  messages: ChatState["messages"];
  isLoading: ChatState["isLoading"];
  error: ChatState["error"];
  send: ChatState["send"];
  selectedData?: DataBlock | null;
  onSelectData?: (data: DataBlock) => void;
}

export function ChatPanel({ title, sidebarOpen, onToggleSidebar, messages, isLoading, error, send, selectedData, onSelectData }: ChatPanelProps) {
  return (
    <PromptInputProvider>
      <ChatPanelInner title={title} sidebarOpen={sidebarOpen} onToggleSidebar={onToggleSidebar} messages={messages} isLoading={isLoading} error={error} send={send} selectedData={selectedData} onSelectData={onSelectData} />
    </PromptInputProvider>
  );
}

function ChatPanelInner({ title, sidebarOpen, onToggleSidebar, messages, isLoading, error, send, selectedData, onSelectData }: ChatPanelProps) {
  const { textInput } = usePromptInputController();
  const isEmpty = textInput.value.trim() === "";

  return (
    <div className="flex h-full flex-col bg-background">
      <PanelHeader>
        <div className="flex items-center gap-1.5">
          {!sidebarOpen && (
            <Button variant="ghost" size="icon-sm" onClick={onToggleSidebar}>
              <PanelLeftIcon />
            </Button>
          )}
          <div className="flex min-w-0 flex-1 items-center gap-1.5">
            <MessageCircleIcon className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate text-sm font-medium">{title}</span>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon-sm">
                <EllipsisIcon />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem>
                <Trash2Icon />
                Remove chat
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </PanelHeader>
      <Conversation className="relative min-h-0 flex-1">
        <ConversationContent className="mx-auto max-w-[700px] gap-12 pb-12">
          {messages.map((msg, i) => {
            const isModel = msg.role === "model";
            const isLast = i === messages.length - 1;
            return (
              <Message from={msg.role === "user" ? "user" : "assistant"} key={msg.id}>
                <MessageContent>
                  {parseContent(msg).map((seg, j) =>
                    seg.type === "text" ? (
                      <MessageResponse key={`text-${j}`}>{seg.text}</MessageResponse>
                    ) : (
                      <DataCard key={`data-${seg.index}`} data={seg.block} active={selectedData === seg.block} onClick={() => onSelectData?.(seg.block)} />
                    ),
                  )}
                </MessageContent>
                {isModel && (
                  <MessageActions
                    className={
                      isLast
                        ? ""
                        : "opacity-0 transition-opacity group-hover:opacity-100 lg:opacity-0 max-lg:opacity-100"
                    }
                  >
                    <MessageAction tooltip="Like">
                      <ThumbsUpIcon />
                    </MessageAction>
                    <MessageAction tooltip="Dislike">
                      <ThumbsDownIcon />
                    </MessageAction>
                  </MessageActions>
                )}
              </Message>
            );
          })}
        </ConversationContent>
        {error && (
          <div className="mx-4 rounded bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
        <ConversationScrollButton />
      </Conversation>
      <div className="mx-auto w-full max-w-[740px] px-4 pb-8">
        <PromptInput onSubmit={(message) => { send(message.text); }}>
          <PromptInputBody>
            <PromptInputTextarea />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputSubmit className="ml-auto" disabled={isEmpty || isLoading} />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </div>
  );
}
