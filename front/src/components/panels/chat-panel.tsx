import { Conversation, ConversationContent, ConversationEmptyState, ConversationScrollButton } from "@/components/ai/conversation";
import { DataCard } from "@/components/ai/data-card";
import { Loader } from "@/components/ai/loader";
import { Message, MessageAction, MessageActions, MessageContent, MessageResponse } from "@/components/ai/message";
import { StrategyCard } from "@/components/ai/strategy-card";
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
import { parseContent } from "@/lib/parse-content";
import type { DataBlock } from "@/types";

interface ChatPanelProps {
  header?: React.ReactNode;
  messages: ChatState["messages"];
  isLoading: ChatState["isLoading"];
  send: ChatState["send"];
  selectedData?: DataBlock | null;
  onSelectData?: (data: DataBlock) => void;
  pendingTool?: ChatState["pendingTool"];
  confirmBacktest?: ChatState["confirmBacktest"];
  dismissBacktest?: ChatState["dismissBacktest"];
}

export function ChatPanel({ header, messages, isLoading, send, selectedData, onSelectData, pendingTool, confirmBacktest, dismissBacktest }: ChatPanelProps) {
  return (
    <PromptInputProvider>
      <ChatPanelInner header={header} messages={messages} isLoading={isLoading} send={send} selectedData={selectedData} onSelectData={onSelectData} pendingTool={pendingTool} confirmBacktest={confirmBacktest} dismissBacktest={dismissBacktest} />
    </PromptInputProvider>
  );
}

function ChatPanelInner({ header, messages, isLoading, send, selectedData, onSelectData, pendingTool, confirmBacktest, dismissBacktest }: ChatPanelProps) {
  const { textInput } = usePromptInputController();
  const isEmpty = textInput.value.trim() === "";

  return (
    <div className="flex h-full flex-col bg-background">
      {header}
      <Conversation className="relative min-h-0 flex-1">
        {messages.length === 0 && !isLoading ? (
          <ConversationEmptyState
            title="No messages yet"
            description="Ask a question to get started"
          />
        ) : (
        <ConversationContent className="mx-auto max-w-[700px] gap-12 pb-12">
          {messages.map((msg, i) => {
            const isModel = msg.role === "model";
            const isLast = i === messages.length - 1;
            const hasPendingTool = pendingTool?.messageId === msg.id;
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
                  {hasPendingTool && confirmBacktest && (
                    <StrategyCard
                      input={pendingTool.input}
                      onConfirm={confirmBacktest}
                      onCancel={dismissBacktest ?? (() => {})}
                      isRunning={isLoading}
                    />
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
          {isLoading && messages.length > 0 && messages[messages.length - 1].role === "user" && (
            <Message from="assistant">
              <MessageContent>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader size={16} />
                  <span className="text-sm">Thinking...</span>
                </div>
              </MessageContent>
            </Message>
          )}
        </ConversationContent>
        )}
        <ConversationScrollButton />
      </Conversation>
      <div className="mx-auto w-full max-w-[740px] px-4 pb-8">
        <PromptInput onSubmit={(message) => send(message.text)}>
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
