import { useNavigate, useParams } from "react-router-dom";
import { MessageCirclePlusIcon, PanelLeftIcon } from "lucide-react";
import { SidebarPanel } from "@/components/panels/sidebar-panel";
import { ResizeHandle } from "@/components/panels/resize-handle";
import { PanelHeader } from "@/components/panels/panel-header";
import { Button } from "@/components/ui/button";
import { useConversations } from "@/hooks/use-conversations";
import { useInstruments } from "@/hooks/use-instruments";
import { usePanelLayout } from "@/hooks/use-panel-layout";
import { useSidebar } from "@/hooks/use-sidebar";

export function InstrumentPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const { instruments } = useInstruments();
  const { conversations: allConversations, loading, create } = useConversations();
  const conversations = allConversations.filter((c) => c.instrument === symbol);
  const navigate = useNavigate();
  const { sidebarWidth, onSidebarResize } = usePanelLayout();
  const { sidebarOpen, toggleSidebar } = useSidebar();

  const instrument = instruments.find((i) => i.instrument === symbol);

  const handleNewChat = async () => {
    if (!symbol) return;
    const conv = await create(symbol);
    navigate(`/i/${symbol}/c/${conv.id}`);
  };

  return (
    <div className="flex h-full">
      {sidebarOpen && (
        <>
          <div
            style={{ "--sidebar-w": `${sidebarWidth}px` } as React.CSSProperties}
            className="w-[80vw] shrink-0 lg:w-(--sidebar-w)"
          >
            <SidebarPanel onCollapse={toggleSidebar} />
          </div>
          <ResizeHandle className="hidden lg:block" onResize={onSidebarResize} />
        </>
      )}
      <div className="min-w-full flex-1 lg:min-w-0">
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
        <div className="p-4">
          <Button onClick={handleNewChat}>
            <MessageCirclePlusIcon />
            New chat
          </Button>
          {loading ? (
            <div className="mt-4 text-sm text-muted-foreground">Loading...</div>
          ) : (
            <div className="mt-4 flex flex-col gap-2">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  className="rounded-lg border p-3 text-left hover:bg-accent"
                  onClick={() => navigate(`/i/${symbol}/c/${conv.id}`)}
                >
                  <div className="text-sm font-medium">{conv.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </div>
                </button>
              ))}
              {conversations.length === 0 && (
                <div className="text-sm text-muted-foreground">
                  No conversations yet. Start a new chat!
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
