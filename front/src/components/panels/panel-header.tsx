import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type PanelHeaderProps = HTMLAttributes<HTMLDivElement>;

export function PanelHeader({ className, ...props }: PanelHeaderProps) {
  return (
    <div
      className={cn("flex min-h-[45px] items-center justify-between px-2 py-2", className)}
      {...props}
    />
  );
}
