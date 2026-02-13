import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const SIZE = {
  xs: "size-5 text-[10px]",
  sm: "size-6 text-xs",
  default: "size-8 text-sm",
  lg: "size-10 text-sm",
} as const;

interface AvatarProps {
  src?: string | null;
  fallback?: ReactNode;
  size?: keyof typeof SIZE;
  alt?: string;
  className?: string;
}

export function Avatar({ src, fallback, size = "default", alt = "", className }: AvatarProps) {
  return (
    <span className={cn("relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full select-none", SIZE[size], className)}>
      {src ? (
        <img src={src} alt={alt} className="size-full object-cover" />
      ) : (
        <span className="flex size-full items-center justify-center bg-muted text-muted-foreground">
          {fallback}
        </span>
      )}
    </span>
  );
}
