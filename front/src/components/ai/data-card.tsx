import { TableIcon } from "lucide-react";
import type { DataBlock } from "@/types";

interface DataCardProps {
  data: DataBlock;
  onClick?: () => void;
}

function formatLabel(data: DataBlock): string {
  const parts: string[] = [];
  if (data.session) parts.push(data.session);
  if (data.timeframe) parts.push(data.timeframe);
  if (data.rows !== null) parts.push(`${data.rows} rows`);
  return parts.join(" · ") || "Query result";
}

export function DataCard({ data, onClick }: DataCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-fit items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
    >
      <TableIcon className="size-4 shrink-0" />
      <span>{formatLabel(data)}</span>
    </button>
  );
}
