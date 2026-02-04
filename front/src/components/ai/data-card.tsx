import { TableIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DataBlock } from "@/types";

interface DataCardProps {
  data: DataBlock;
  active?: boolean;
  onClick?: () => void;
}

export function formatLabel(data: DataBlock): string {
  const parts: string[] = [];
  if (data.session) parts.push(data.session);
  if (data.timeframe) parts.push(data.timeframe);
  if (data.rows !== null) parts.push(`${data.rows} rows`);
  return parts.join(" · ") || "Query result";
}

export function DataCard({ data, active, onClick }: DataCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-fit items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
        active && "bg-accent text-foreground",
      )}
    >
      <TableIcon className="size-4 shrink-0" />
      <span>{formatLabel(data)}</span>
    </button>
  );
}
