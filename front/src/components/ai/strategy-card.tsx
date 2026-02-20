import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { format, parse } from "date-fns";
import type { DateRange } from "react-day-picker";
import { CalendarIcon, ChevronDownIcon, LoaderIcon, PlayIcon, XIcon } from "lucide-react";
import { useOHLC } from "@/hooks/use-ohlc";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
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
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
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

/** Parse partial date "YYYY" | "YYYY-MM" | "YYYY-MM-DD" into a Date */
function parsePartialDate(s: string, end: boolean): Date | undefined {
  // "2023" → Jan 1 or Dec 31
  if (/^\d{4}$/.test(s)) {
    return end ? new Date(+s, 11, 31) : new Date(+s, 0, 1);
  }
  // "2023-06" → Jun 1 or Jun 30
  if (/^\d{4}-\d{2}$/.test(s)) {
    const [y, m] = s.split("-").map(Number);
    return end ? new Date(y, m, 0) : new Date(y, m - 1, 1); // day 0 = last day of prev month
  }
  // "2023-06-15"
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    return parse(s, "yyyy-MM-dd", new Date());
  }
  return undefined;
}

/** Parse "YYYY:YYYY", "YYYY-MM:YYYY-MM", or "YYYY-MM-DD:YYYY-MM-DD" into DateRange */
function parsePeriod(period: string): DateRange | undefined {
  if (!period) return undefined;
  const parts = period.split(":");
  if (parts.length !== 2) return undefined;
  const from = parsePartialDate(parts[0], false);
  const to = parsePartialDate(parts[1], true);
  if (!from || !to) return undefined;
  return { from, to };
}

function formatPeriodLabel(range: DateRange | undefined): string {
  if (!range?.from) return "";
  const from = format(range.from, "MMM d, yyyy");
  if (!range.to) return from;
  return `${from} — ${format(range.to, "MMM d, yyyy")}`;
}

function DateRangePicker({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const { symbol } = useParams<{ symbol: string }>();
  const { data: ohlc } = useOHLC(symbol);
  const [open, setOpen] = useState(false);
  const range = useMemo(() => parsePeriod(value), [value]);

  // Restrict calendar to actual data range
  const dataRange = useMemo(() => {
    if (!ohlc || ohlc.length === 0) return undefined;
    return {
      from: new Date(ohlc[0].time),
      to: new Date(ohlc[ohlc.length - 1].time),
    };
  }, [ohlc]);

  const handleSelect = (selected: DateRange | undefined) => {
    if (!selected?.from) {
      onChange("");
      return;
    }
    const from = format(selected.from, "yyyy-MM-dd");
    const to = selected.to ? format(selected.to, "yyyy-MM-dd") : from;
    onChange(`${from}:${to}`);
  };

  const label = formatPeriodLabel(range);

  return (
    <div className="flex gap-1">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            disabled={disabled}
            className="border-input flex h-9 w-full items-center gap-2 rounded-md border bg-background px-3 text-sm outline-none disabled:pointer-events-none disabled:opacity-50"
          >
            <CalendarIcon className="text-muted-foreground size-4 shrink-0" />
            <span className={label ? "truncate" : "text-muted-foreground"}>
              {label || "All data"}
            </span>
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="range"
            selected={range}
            onSelect={handleSelect}
            defaultMonth={range?.from}
            numberOfMonths={2}
            disabled={dataRange
              ? { before: dataRange.from, after: dataRange.to }
              : { after: new Date() }
            }
          />
        </PopoverContent>
      </Popover>
      {value && !disabled && (
        <Button
          variant="ghost"
          size="icon-xs"
          className="shrink-0 self-center"
          onClick={() => onChange("")}
        >
          <XIcon />
        </Button>
      )}
    </div>
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
          <DateRangePicker
            value={String(params.period ?? "")}
            onChange={(v) => updateParam("period", v)}
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
