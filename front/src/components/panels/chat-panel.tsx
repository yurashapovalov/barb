import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai/conversation";
import { Message, MessageContent } from "@/components/ai/message";
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

const messages = [
  { id: "1", from: "user" as const, text: "Hello, how are you?" },
  { id: "2", from: "assistant" as const, text: "I'm good, thank you! How can I assist you today?" },
  { id: "3", from: "user" as const, text: "I'm looking for information about your services." },
  { id: "4", from: "assistant" as const, text: "Sure! We offer a variety of AI solutions. What are you interested in?" },
];

export function ChatPanel() {
  const handleSubmit = () => {
    // TODO: send message
  };

  return (
    <div className="relative h-full rounded-none bg-background lg:rounded">
      <Conversation className="relative size-full p-4">
        <ConversationContent>
          {messages.map(msg => (
            <Message from={msg.from} key={msg.id}>
              <MessageContent>{msg.text}</MessageContent>
            </Message>
          ))}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>
      <div className="absolute inset-x-0 bottom-0 z-10 p-4">
        <PromptInput multiple onSubmit={handleSubmit}>
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
