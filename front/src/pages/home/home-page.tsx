import { PanelLeftIcon } from "lucide-react";
import { HomePanel } from "@/components/panels/home-panel";
import { PanelHeader } from "@/components/panels/panel-header";
import { Button } from "@/components/ui/button";
import { useSidebar } from "@/hooks/use-sidebar";

export function HomePage() {
  const { sidebarOpen, toggleSidebar } = useSidebar();

  const header = (
    <PanelHeader>
      {!sidebarOpen && (
        <Button variant="ghost" size="icon-sm" onClick={toggleSidebar}>
          <PanelLeftIcon />
        </Button>
      )}
    </PanelHeader>
  );

  return <HomePanel header={header} />;
}
