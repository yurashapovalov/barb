import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai/conversation";
import { Message, MessageContent, MessageResponse } from "@/components/ai/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputTools,
  PromptInputActionMenu,
  PromptInputActionMenuTrigger,
  PromptInputActionMenuContent,
  PromptInputActionAddAttachments,
  PromptInputAttachments,
  PromptInputAttachment,
  PromptInputSubmit,
} from "@/components/ai/prompt-input";
import type { ChatState } from "@/hooks/use-chat";

interface ChatPanelProps {
  messages: ChatState["messages"];
  error: ChatState["error"];
  send: ChatState["send"];
}

export function ChatPanel({ messages, error, send }: ChatPanelProps) {
  return (
    <div className="flex h-full flex-col bg-background">
      <Conversation className="relative min-h-0 flex-1">
        <ConversationContent className="mx-auto max-w-[700px] pb-12">
          {messages.map((msg) => (
            <Message from={msg.role === "user" ? "user" : "assistant"} key={msg.id}>
              <MessageContent>
                <MessageResponse>{msg.content}</MessageResponse>
              </MessageContent>
            </Message>
          ))}
        </ConversationContent>
        {error && (
          <div className="mx-4 rounded bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
        <ConversationScrollButton />
      </Conversation>
      <div className="mx-auto w-full max-w-[740px] px-4 pb-8">
        <PromptInput multiple onSubmit={(message) => send(message.text)}>
          <PromptInputAttachments>
            {(attachment) => <PromptInputAttachment data={attachment} />}
          </PromptInputAttachments>
          <PromptInputBody>
            <PromptInputTextarea />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputTools>
              <PromptInputActionMenu>
                <PromptInputActionMenuTrigger />
                <PromptInputActionMenuContent>
                  <PromptInputActionAddAttachments />
                </PromptInputActionMenuContent>
              </PromptInputActionMenu>
            </PromptInputTools>
            <PromptInputSubmit />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </div>
  );
}
