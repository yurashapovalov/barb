import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai/conversation";
import { DataCard } from "@/components/ai/data-card";
import { Message, MessageAction, MessageActions, MessageContent, MessageResponse } from "@/components/ai/message";
import { ThumbsDownIcon, ThumbsUpIcon } from "lucide-react";
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputProvider,
  PromptInputSubmit,
  usePromptInputController,
} from "@/components/ai/prompt-input";
import type { ChatState } from "@/hooks/use-chat";
import type { DataBlock, Message as MessageType } from "@/types";
import { PanelHeader } from "./panel-header";

type ContentSegment =
  | { type: "text"; text: string }
  | { type: "data"; block: DataBlock; index: number };

const DATA_MARKER = /\{\{data:(\d+)\}\}/g;

function parseContent(msg: MessageType): ContentSegment[] {
  if (!msg.data?.length) {
    return [{ type: "text", text: msg.content }];
  }

  const segments: ContentSegment[] = [];
  let lastIndex = 0;

  for (const match of msg.content.matchAll(DATA_MARKER)) {
    const before = msg.content.slice(lastIndex, match.index);
    if (before.trim()) segments.push({ type: "text", text: before });
    const blockIndex = Number(match[1]);
    if (msg.data[blockIndex]) {
      segments.push({ type: "data", block: msg.data[blockIndex], index: blockIndex });
    }
    lastIndex = match.index + match[0].length;
  }

  const after = msg.content.slice(lastIndex);
  if (after.trim()) segments.push({ type: "text", text: after });

  // No markers found — cards at the end (historical messages from API)
  if (segments.every((s) => s.type === "text")) {
    for (let i = 0; i < msg.data.length; i++) {
      segments.push({ type: "data", block: msg.data[i], index: i });
    }
  }

  return segments;
}

interface ChatPanelProps {
  messages: ChatState["messages"];
  isLoading: ChatState["isLoading"];
  error: ChatState["error"];
  send: ChatState["send"];
}

export function ChatPanel({ messages, isLoading, error, send }: ChatPanelProps) {
  return (
    <PromptInputProvider>
      <ChatPanelInner messages={messages} isLoading={isLoading} error={error} send={send} />
    </PromptInputProvider>
  );
}

function ChatPanelInner({ messages, isLoading, error, send }: ChatPanelProps) {
  const { textInput } = usePromptInputController();
  const isEmpty = textInput.value.trim() === "";

  return (
    <div className="flex h-full flex-col bg-background">
      <PanelHeader />
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
                      <MessageResponse key={j}>{seg.text}</MessageResponse>
                    ) : (
                      <DataCard key={`data-${seg.index}`} data={seg.block} />
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
        <PromptInput multiple onSubmit={(message) => { send(message.text); }}>
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
