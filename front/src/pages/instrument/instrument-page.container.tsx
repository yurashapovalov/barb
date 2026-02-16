import { useNavigate, useParams } from "react-router-dom";
import { PanelLeftIcon } from "lucide-react";
import { InstrumentPanel } from "@/components/panels/instrument/instrument-panel";
import { PanelHeader } from "@/components/panels/panel-header";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useConversations } from "@/hooks/use-conversations";
import { useInstruments } from "@/hooks/use-instruments";
import { useOHLC } from "@/hooks/use-ohlc";
import { useSidebar } from "@/hooks/use-sidebar";

export function InstrumentPageContainer() {
  const { symbol } = useParams<{ symbol: string }>();
  const { instruments } = useInstruments();
  const { conversations: allConversations, loading, remove } = useConversations();
  const conversations = allConversations.filter((c) => c.instrument === symbol);
  const navigate = useNavigate();
  const { sidebarOpen, toggleSidebar } = useSidebar();
  const { data: ohlcData, loading: ohlcLoading } = useOHLC(symbol);

  const instrument = instruments.find((i) => i.instrument === symbol);

  const handleSend = (text: string) => {
    if (!symbol) return;
    sessionStorage.setItem("barb:initial-msg", text);
    navigate(`/i/${symbol}/c/new`);
  };

  const header = (
    <PanelHeader>
      <div className="flex items-center gap-2">
        {!sidebarOpen && (
          <Button variant="ghost" size="icon-sm" onClick={toggleSidebar} aria-label="Open sidebar">
            <PanelLeftIcon />
          </Button>
        )}
        <Avatar size="xs" src={instrument?.image_url ?? undefined} fallback={symbol?.slice(0, 2) ?? ""} />
        <span className="text-sm font-medium">
          {instrument?.name ?? symbol}
          {instrument?.exchange && <span className="text-muted-foreground"> {instrument.exchange}</span>}
        </span>
      </div>
    </PanelHeader>
  );

  return (
    <InstrumentPanel
      header={header}
      ohlcData={ohlcData}
      ohlcLoading={ohlcLoading}
      conversations={conversations}
      loading={loading}
      onSend={handleSend}
      onSelectChat={(conv) => navigate(`/i/${symbol}/c/${conv.id}`)}
      onRemoveChat={remove}
    />
  );
}
