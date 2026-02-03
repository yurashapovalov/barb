import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type PanelHeaderProps = HTMLAttributes<HTMLDivElement>;

export function PanelHeader({ className, ...props }: PanelHeaderProps) {
  return (
    <div
      className={cn("flex items-center justify-between px-4 py-2", className)}
      {...props}
    />
  );
}
