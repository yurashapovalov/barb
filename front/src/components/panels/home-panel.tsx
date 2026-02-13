import type { ReactNode } from "react";

interface HomePanelProps {
  header: ReactNode;
}

export function HomePanel({ header }: HomePanelProps) {
  return (
    <div className="flex h-full flex-col bg-background">
      {header}
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Select a symbol to get started</p>
      </div>
    </div>
  );
}
