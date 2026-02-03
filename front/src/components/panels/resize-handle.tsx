import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface ResizeHandleProps {
  onResize: (delta: number) => void;
  className?: string;
}

export function ResizeHandle({ onResize, className }: ResizeHandleProps) {
  const lastX = useRef(0);
  const cleanupRef = useRef<(() => void) | null>(null);

  // Clean up listeners if component unmounts mid-drag
  useEffect(() => {
    return () => cleanupRef.current?.();
  }, []);

  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    lastX.current = e.clientX;

    const onMouseMove = (ev: MouseEvent) => {
      const delta = ev.clientX - lastX.current;
      lastX.current = ev.clientX;
      onResize(delta);
    };

    const cleanup = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", cleanup);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      cleanupRef.current = null;
    };

    // If somehow a previous drag wasn't cleaned up, do it now
    cleanupRef.current?.();

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", cleanup);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    cleanupRef.current = cleanup;
  };

  return (
    <div
      onMouseDown={onMouseDown}
      className={cn(
        "relative w-px shrink-0 cursor-col-resize bg-border before:absolute before:inset-y-0 before:-left-1.5 before:-right-1.5",
        className,
      )}
    />
  );
}
