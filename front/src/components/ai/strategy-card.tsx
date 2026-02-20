import { useState } from "react";
import { LoaderIcon, PlayIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface StrategyCardProps {
  input: Record<string, unknown>;
  onConfirm: (input: Record<string, unknown>) => void;
  onCancel: () => void;
  isRunning: boolean;
}

const STRATEGY_FIELDS = [
  { key: "direction", label: "Direction" },
  { key: "stop_loss", label: "Stop Loss" },
  { key: "take_profit", label: "Take Profit" },
  { key: "trailing_stop", label: "Trailing Stop" },
  { key: "breakeven_bars", label: "Breakeven (bars)" },
  { key: "exit_bars", label: "Exit (bars)" },
  { key: "exit_target", label: "Exit Target" },
  { key: "slippage", label: "Slippage" },
  { key: "commission", label: "Commission" },
] as const;

// Fields shown even if not in the original input
const ALWAYS_VISIBLE = new Set(["direction", "stop_loss", "take_profit"]);

export function StrategyCard({ input, onConfirm, onCancel, isRunning }: StrategyCardProps) {
  const [params, setParams] = useState(() => structuredClone(input));

  const strategy = (params.strategy ?? {}) as Record<string, unknown>;
  const entryLabel = (strategy.entry_label ?? strategy.entry ?? "") as string;
  const title = (params.title ?? "Backtest") as string;

  const updateStrategy = (key: string, value: string) => {
    setParams((prev) => ({
      ...prev,
      strategy: { ...(prev.strategy as Record<string, unknown>), [key]: value || undefined },
    }));
  };

  const updateParam = (key: string, value: string) => {
    setParams((prev) => ({ ...prev, [key]: value || undefined }));
  };

  const visibleFields = STRATEGY_FIELDS.filter(
    (f) => strategy[f.key] !== undefined || ALWAYS_VISIBLE.has(f.key),
  );

  return (
    <div className="my-2 w-full">
      <div className="mb-3 text-lg font-medium tracking-tight">{title}</div>

      <div className="mb-3 space-y-2">
        <div className="flex items-start gap-3">
          <span className="shrink-0 pt-2 text-sm text-muted-foreground">Entry</span>
          <Textarea
            className="min-h-9 resize-none text-sm"
            value={entryLabel}
            disabled
            rows={1}
          />
        </div>

        {visibleFields.map(({ key, label }) => (
          <div key={key} className="flex items-center gap-3">
            <span className="shrink-0 text-sm text-muted-foreground">{label}</span>
            <Input
              className="h-8 text-sm"
              value={String(strategy[key] ?? "")}
              onChange={(e) => updateStrategy(key, e.target.value)}
              disabled={isRunning}
            />
          </div>
        ))}

        <div className="flex items-center gap-3">
          <span className="shrink-0 text-sm text-muted-foreground">Session</span>
          <Input
            className="h-8 text-sm"
            value={String(params.session ?? "")}
            onChange={(e) => updateParam("session", e.target.value)}
            disabled={isRunning}
          />
        </div>
        <div className="flex items-center gap-3">
          <span className="shrink-0 text-sm text-muted-foreground">Period</span>
          <Input
            className="h-8 text-sm"
            value={String(params.period ?? "")}
            onChange={(e) => updateParam("period", e.target.value)}
            disabled={isRunning}
          />
        </div>
      </div>

      <div className="flex gap-2">
        <Button className="flex-1" size="sm" onClick={() => onConfirm(params)} disabled={isRunning}>
          {isRunning ? (
            <>
              <LoaderIcon className="animate-spin" />
              Running...
            </>
          ) : (
            <>
              <PlayIcon />
              Run Backtest
            </>
          )}
        </Button>
        {!isRunning && (
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
}
