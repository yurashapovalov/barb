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
  const { conversations: allConversations, loading, create } = useConversations();
  const conversations = allConversations.filter((c) => c.instrument === symbol);
  const navigate = useNavigate();
  const { sidebarOpen, toggleSidebar } = useSidebar();

  const instrument = instruments.find((i) => i.instrument === symbol);

  const handleNewChat = async () => {
    if (!symbol) return;
    const conv = await create(symbol);
    navigate(`/i/${symbol}/c/${conv.id}`);
  };

  const header = (
    <PanelHeader>
      <div className="flex items-center gap-2">
        {!sidebarOpen && (
          <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
            <PanelLeftIcon />
          </Button>
        )}
        {instrument?.image_url && (
          <img src={instrument.image_url} alt="" className="size-5 rounded-full" />
        )}
        <span className="font-medium">{symbol}</span>
        {instrument && (
          <span className="text-muted-foreground">· {instrument.name}</span>
        )}
      </div>
    </PanelHeader>
  );

  return (
    <InstrumentPanel
      header={header}
      conversations={conversations}
      loading={loading}
      onNewChat={handleNewChat}
      onSelectChat={(conv) => navigate(`/i/${symbol}/c/${conv.id}`)}
    />
  );
}
