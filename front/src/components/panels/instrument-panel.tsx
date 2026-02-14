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
import { Avatar } from "@/components/ui/avatar";
import type { OHLCBar } from "@/lib/api";
import type { Conversation } from "@/types";

interface InstrumentPanelProps {
  header: ReactNode;
  symbol: string;
  name?: string;
  exchange?: string;
  imageUrl?: string;
  ohlcData?: OHLCBar[] | null;
  ohlcLoading?: boolean;
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

function InstrumentPanelInner({ header, symbol, name, exchange, imageUrl, ohlcData, ohlcLoading, conversations, loading, onSend, onSelectChat }: InstrumentPanelProps) {
  const { textInput } = usePromptInputController();
  const isEmpty = textInput.value.trim() === "";

  return (
    <div className="flex h-full flex-col bg-background">
      {header}
      <div className="flex-1 overflow-y-auto px-4">
        <div className="relative mb-6">
          <div className="absolute left-0 top-0 z-10 flex items-center gap-3 p-3">
            <Avatar size="lg" src={imageUrl} fallback={symbol.slice(0, 2)} />
            <h1 className="text-xl font-semibold">
              {name}
              {exchange && <span> {exchange}</span>}
            </h1>
          </div>
          {ohlcData ? (
            <CandlestickChart data={ohlcData} />
          ) : ohlcLoading ? (
            <div className="flex h-[400px] items-center justify-center">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
            </div>
          ) : null}
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
