import { useNavigate, useParams } from "react-router-dom";
import { PanelLeftIcon } from "lucide-react";
import { InstrumentPanel } from "@/components/panels/instrument-panel";
import { PanelHeader } from "@/components/panels/panel-header";
import { Button } from "@/components/ui/button";
import { useConversations } from "@/hooks/use-conversations";
import { useInstruments } from "@/hooks/use-instruments";
import { useSidebar } from "@/hooks/use-sidebar";

export function InstrumentPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const { instruments } = useInstruments();
  const { conversations: allConversations, loading } = useConversations();
  const conversations = allConversations.filter((c) => c.instrument === symbol);
  const navigate = useNavigate();
  const { sidebarOpen, toggleSidebar } = useSidebar();

  const instrument = instruments.find((i) => i.instrument === symbol);

  const handleSend = (text: string) => {
    if (!symbol) return;
    navigate(`/i/${symbol}/c/new`, { state: { initialMessage: text } });
  };

  const header = (
    <PanelHeader>
      {!sidebarOpen && (
        <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
          <PanelLeftIcon />
        </Button>
      )}
    </PanelHeader>
  );

  return (
    <InstrumentPanel
      header={header}
      symbol={symbol ?? ""}
      name={instrument?.name}
      exchange={instrument?.exchange}
      imageUrl={instrument?.image_url ?? undefined}
      conversations={conversations}
      loading={loading}
      onSend={handleSend}
      onSelectChat={(conv) => navigate(`/i/${symbol}/c/${conv.id}`)}
    />
  );
}
