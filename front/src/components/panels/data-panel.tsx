import { PanelHeader } from "./panel-header";

export function DataPanel() {
  return (
    <div className="flex h-full flex-col bg-background">
      <PanelHeader />
      <div className="flex-1 overflow-y-auto" />
    </div>
  );
}
