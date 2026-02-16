import { Children, Fragment, type ReactNode } from "react";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

interface DividedListProps {
  children: ReactNode;
  className?: string;
}

export function DividedList({ children, className }: DividedListProps) {
  const items = Children.toArray(children).filter(Boolean);
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      {items.map((child, i) => (
        <Fragment key={i}>
          {i > 0 && <Separator />}
          {child}
        </Fragment>
      ))}
    </div>
  );
}
