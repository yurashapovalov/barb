import { useState } from "react";
import { LoaderIcon, PlayIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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
    <div className="my-2 w-full max-w-md rounded-lg border border-border bg-card p-4">
      <div className="mb-3 text-sm font-medium">{title}</div>

      <div className="mb-3 rounded-md bg-muted px-3 py-2 text-sm">
        <span className="text-muted-foreground">Entry: </span>
        {entryLabel}
      </div>

      <div className="mb-3 grid grid-cols-2 gap-2">
        {visibleFields.map(({ key, label }) => (
          <label key={key} className="text-xs text-muted-foreground">
            {label}
            <Input
              className="mt-0.5 h-8 text-sm"
              value={String(strategy[key] ?? "")}
              onChange={(e) => updateStrategy(key, e.target.value)}
              disabled={isRunning}
            />
          </label>
        ))}
      </div>

      <div className="mb-3 grid grid-cols-2 gap-2">
        <label className="text-xs text-muted-foreground">
          Session
          <Input
            className="mt-0.5 h-8 text-sm"
            value={String(params.session ?? "")}
            onChange={(e) => updateParam("session", e.target.value)}
            disabled={isRunning}
          />
        </label>
        <label className="text-xs text-muted-foreground">
          Period
          <Input
            className="mt-0.5 h-8 text-sm"
            value={String(params.period ?? "")}
            onChange={(e) => updateParam("period", e.target.value)}
            disabled={isRunning}
          />
        </label>
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
