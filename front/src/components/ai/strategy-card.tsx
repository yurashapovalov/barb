import { useState } from "react";
import { ChevronDownIcon, LoaderIcon, PlayIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DividedList } from "@/components/ui/divided-list";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center py-2">
      <div className="w-[35%] shrink-0 text-sm">{label}</div>
      <div className="w-[65%]">{children}</div>
    </div>
  );
}

function SelectField({
  value,
  options,
  onChange,
  disabled,
  allowClear,
}: {
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  disabled?: boolean;
  allowClear?: boolean;
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        disabled={disabled}
        className="border-input flex h-9 w-full items-center justify-between rounded-md border bg-background px-3 text-sm outline-none disabled:pointer-events-none disabled:opacity-50"
      >
        <span className={value ? "" : "text-muted-foreground"}>
          {value || "—"}
        </span>
        <ChevronDownIcon className="text-muted-foreground size-4" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuRadioGroup value={value} onValueChange={onChange}>
          {options.map((opt) => (
            <DropdownMenuRadioItem key={opt.value} value={opt.value}>
              {opt.label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
        {allowClear && value && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => onChange("")}>
              Clear
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

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

      <DividedList className="mb-3">
        <FieldRow label="Entry">
          <Textarea
            className="min-h-9 resize-none text-sm"
            value={entryLabel}
            disabled
            rows={1}
          />
        </FieldRow>

        {visibleFields.map(({ key, label }) => (
          <FieldRow key={key} label={label}>
            {key === "direction" ? (
              <SelectField
                value={String(strategy[key] ?? "")}
                options={[
                  { value: "long", label: "long" },
                  { value: "short", label: "short" },
                ]}
                onChange={(v) => updateStrategy(key, v)}
                disabled={isRunning}
              />
            ) : (
              <Input
                className="h-9 text-sm"
                value={String(strategy[key] ?? "")}
                onChange={(e) => updateStrategy(key, e.target.value)}
                disabled={isRunning}
              />
            )}
          </FieldRow>
        ))}

        <FieldRow label="Session">
          <SelectField
            value={String(params.session ?? "")}
            options={[
              { value: "RTH", label: "RTH" },
              { value: "ETH", label: "ETH" },
            ]}
            onChange={(v) => updateParam("session", v)}
            disabled={isRunning}
            allowClear
          />
        </FieldRow>
        <FieldRow label="Period">
          <Input
            className="h-9 text-sm"
            value={String(params.period ?? "")}
            onChange={(e) => updateParam("period", e.target.value)}
            disabled={isRunning}
          />
        </FieldRow>
      </DividedList>

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
