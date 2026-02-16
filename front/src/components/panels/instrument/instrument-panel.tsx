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
import { CandlestickChart } from "@/components/charts/candlestick-chart";
import { ConversationItem } from "./conversation-item";
import { DividedList } from "@/components/ui/divided-list";
import type { OHLCBar } from "@/lib/api";
import type { Conversation } from "@/types";

interface InstrumentPanelProps {
  header: ReactNode;
  ohlcData?: OHLCBar[] | null;
  ohlcLoading?: boolean;
  conversations: Conversation[];
  loading: boolean;
  onSend: (text: string) => void;
  onSelectChat: (conv: Conversation) => void;
  onRemoveChat: (id: string) => Promise<void>;
}

export function InstrumentPanel(props: InstrumentPanelProps) {
  return (
    <PromptInputProvider>
      <InstrumentPanelInner {...props} />
    </PromptInputProvider>
  );
}

function InstrumentPanelInner({ header, ohlcData, ohlcLoading, conversations, loading, onSend, onSelectChat, onRemoveChat }: InstrumentPanelProps) {
  const { textInput } = usePromptInputController();
  const isEmpty = textInput.value.trim() === "";

  return (
    <div className="flex h-full flex-col">
      {header}
      <div className="flex-1 overflow-y-auto px-4">
        <div className="mb-6">
          {ohlcData ? (
            <CandlestickChart data={ohlcData} />
          ) : ohlcLoading ? (
            <div className="flex h-[400px] items-center justify-center">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
            </div>
          ) : null}
        </div>
        <div className="mx-auto w-full max-w-[740px]">
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading...</div>
          ) : conversations.length > 0 ? (
            <DividedList>
              {conversations.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conversation={conv}
                  onSelect={() => onSelectChat(conv)}
                  onRemove={() => onRemoveChat(conv.id)}
                />
              ))}
            </DividedList>
          ) : (
            <div className="text-sm text-muted-foreground">
              No conversations yet. Ask a question below!
            </div>
          )}
        </div>
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
