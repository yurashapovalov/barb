import type { ReactNode } from "react";
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputProvider,
  PromptInputSubmit,
  usePromptInputController,
} from "@/components/ai/prompt-input";
import type { Conversation } from "@/types";

interface InstrumentPanelProps {
  header: ReactNode;
  name?: string;
  exchange?: string;
  imageUrl?: string;
  conversations: Conversation[];
  loading: boolean;
  onSend: (text: string) => void;
  onSelectChat: (conv: Conversation) => void;
}

export function InstrumentPanel(props: InstrumentPanelProps) {
  return (
    <PromptInputProvider>
      <InstrumentPanelInner {...props} />
    </PromptInputProvider>
  );
}

function InstrumentPanelInner({ header, name, exchange, imageUrl, conversations, loading, onSend, onSelectChat }: InstrumentPanelProps) {
  const { textInput } = usePromptInputController();
  const isEmpty = textInput.value.trim() === "";

  return (
    <div className="flex h-full flex-col bg-background">
      {header}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-6 flex items-center gap-3">
          {imageUrl && (
            <img src={imageUrl} alt="" className="size-12 rounded-full" />
          )}
          <div>
            <h1 className="text-lg font-semibold">{name}</h1>
            {exchange && <p className="text-sm text-muted-foreground">{exchange}</p>}
          </div>
        </div>
        {loading ? (
          <div className="text-sm text-muted-foreground">Loading...</div>
        ) : conversations.length > 0 ? (
          <div className="flex flex-col gap-2">
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
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">
            No conversations yet. Ask a question below!
          </div>
        )}
      </div>
      <div className="mx-auto w-full max-w-[740px] px-4 pb-8">
        <PromptInput onSubmit={(message) => onSend(message.text)}>
          <PromptInputBody>
            <PromptInputTextarea />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputSubmit className="ml-auto" disabled={isEmpty} />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </div>
  );
}
