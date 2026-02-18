import { AlertCircleIcon, LoaderIcon, TableIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DataBlock } from "@/types";

interface DataCardProps {
  data: DataBlock;
  active?: boolean;
  onClick?: () => void;
}

export function formatLabel(data: DataBlock): string {
  if (data.status === "loading") return "Loading...";
  if (data.status === "error") return data.error || "Error";
  return data.title || "Query result";
}

export function DataCard({ data, active, onClick }: DataCardProps) {
  const isLoading = data.status === "loading";
  const isError = data.status === "error";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isLoading}
      className={cn(
        "flex w-fit items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm text-muted-foreground transition-colors",
        !isLoading && "hover:bg-accent hover:text-foreground",
        active && "bg-accent text-foreground",
        isError && "border-destructive/50 text-destructive",
        isLoading && "cursor-wait opacity-70",
      )}
    >
      {isLoading ? (
        <LoaderIcon className="size-4 shrink-0 animate-spin" />
      ) : isError ? (
        <AlertCircleIcon className="size-4 shrink-0" />
      ) : (
        <TableIcon className="size-4 shrink-0" />
      )}
      <span>{formatLabel(data)}</span>
    </button>
  );
}
