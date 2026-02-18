import { useState } from "react";
import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Area, CartesianGrid, ComposedChart, Line, XAxis, YAxis } from "recharts";
import { ArrowDownIcon, ArrowUpIcon, XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatLabel } from "@/components/ai/data-card";
import { BarChart } from "@/components/charts/bar-chart";
import { formatColumnLabel, formatValue } from "@/lib/format";
import type {
  AreaChartBlock,
  BarChartBlock,
  DataBlock,
  HorizontalBarBlock,
  MetricsGridBlock,
  TableBlock,
} from "@/types";
import { PanelHeader } from "./panel-header";

type Row = Record<string, unknown>;

function buildColumns(keys: string[]): ColumnDef<Row>[] {
  return keys.map((key) => ({
    accessorKey: key,
    header: ({ column }) => {
      const sorted = column.getIsSorted();
      const label = formatColumnLabel(key);
      return (
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-1 outline-none">
            {label}
            {sorted === "asc" && <ArrowUpIcon className="size-3" />}
            {sorted === "desc" && <ArrowDownIcon className="size-3" />}
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuItem onClick={() => column.toggleSorting(false)}>
              <ArrowUpIcon className="size-3" />
              Ascending
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => column.toggleSorting(true)}>
              <ArrowDownIcon className="size-3" />
              Descending
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  }));
}

const coreRowModel = getCoreRowModel<Row>();
const sortedRowModel = getSortedRowModel<Row>();

function TableBlockView({ block }: { block: TableBlock }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const columns = buildColumns(block.columns);

  const table = useReactTable({
    data: block.rows,
    columns,
    getCoreRowModel: coreRowModel,
    getSortedRowModel: sortedRowModel,
    onSortingChange: setSorting,
    state: { sorting },
  });

  return (
    <Table className="w-auto mx-6">
      <TableHeader>
        {table.getHeaderGroups().map((group) => (
          <TableRow key={group.id}>
            {group.headers.map((header) => (
              <TableHead key={header.id} className="min-w-[180px]">
                {header.isPlaceholder
                  ? null
                  : flexRender(header.column.columnDef.header, header.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.length ? (
          table.getRowModel().rows.map((row) => (
            <TableRow key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan={columns.length} className="h-24 text-center">
              No data.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

function BarChartBlockView({ block }: { block: BarChartBlock }) {
  return (
    <div className="px-6 pb-4">
      <BarChart
        data={block.rows}
        categoryKey={block.category_key}
        valueKey={block.value_key}
      />
    </div>
  );
}

const COLOR_MAP: Record<string, string> = {
  green: "oklch(0.65 0.2 145)",
  red: "oklch(0.65 0.2 25)",
};

function MetricsGridBlockView({ block }: { block: MetricsGridBlock }) {
  return (
    <div className="grid grid-cols-4 gap-px mx-6 mb-4 rounded-lg border overflow-hidden">
      {block.items.map((item) => (
        <div key={item.label} className="bg-background px-3 py-2.5">
          <div className="text-muted-foreground text-xs">{item.label}</div>
          <div
            className="text-sm font-medium tabular-nums mt-0.5"
            style={item.color ? { color: COLOR_MAP[item.color] ?? item.color } : undefined}
          >
            {item.value}
          </div>
        </div>
      ))}
    </div>
  );
}

const EQUITY_COLOR = "oklch(0.65 0.2 250)";
const DRAWDOWN_COLOR = "oklch(0.65 0.2 25)";

function AreaChartBlockView({ block }: { block: AreaChartBlock }) {
  const config: ChartConfig = {};
  for (const s of block.series) {
    config[s.key] = {
      label: s.label,
      color: s.color === "red" ? DRAWDOWN_COLOR : EQUITY_COLOR,
    };
  }

  return (
    <div className="px-6 pb-4">
      <ChartContainer config={config} className="h-[200px] w-full">
        <ComposedChart data={block.data} margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
          <XAxis
            dataKey={block.x_key}
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            tickFormatter={(v: string) => v.slice(5)}
          />
          <YAxis tickLine={false} axisLine={false} tickMargin={8} width={60} />
          <ChartTooltip
            content={
              <ChartTooltipContent
                formatter={(value) => formatValue(value, { decimals: 1 })}
              />
            }
          />
          {block.series.map((s) =>
            s.style === "area" ? (
              <Area
                key={s.key}
                dataKey={s.key}
                type="monotone"
                fill={config[s.key]?.color}
                fillOpacity={0.15}
                stroke={config[s.key]?.color}
                strokeWidth={1.5}
              />
            ) : (
              <Line
                key={s.key}
                dataKey={s.key}
                type="monotone"
                stroke={config[s.key]?.color}
                strokeWidth={2}
                dot={false}
              />
            ),
          )}
        </ComposedChart>
      </ChartContainer>
    </div>
  );
}

function HorizontalBarBlockView({ block }: { block: HorizontalBarBlock }) {
  const maxAbs = Math.max(...block.items.map((i) => Math.abs(i.value)), 1);

  return (
    <div className="mx-6 mb-4 space-y-2">
      {block.items.map((item) => {
        const isPositive = item.value >= 0;
        const widthPct = (Math.abs(item.value) / maxAbs) * 100;
        const color = isPositive ? "oklch(0.65 0.2 145)" : "oklch(0.65 0.2 25)";

        return (
          <div key={item.label}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span>{item.label}</span>
              <span className="font-medium tabular-nums" style={{ color }}>
                {item.value >= 0 ? "+" : ""}
                {formatValue(item.value, { decimals: 1 })}
              </span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${widthPct}%`, backgroundColor: color }}
              />
            </div>
            {item.detail && (
              <div className="text-xs text-muted-foreground mt-0.5">{item.detail}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}

interface DataPanelProps {
  data: DataBlock;
  onClose: () => void;
}

export function DataPanel({ data, onClose }: DataPanelProps) {
  return (
    <div className="flex h-full flex-col bg-background">
      <PanelHeader>
        <div />
        <Button variant="ghost" size="icon-sm" onClick={onClose} aria-label="Close panel">
          <XIcon className="size-4" />
        </Button>
      </PanelHeader>
      <div className="flex-1 overflow-y-auto">
        <h2 className="px-6 py-4 text-lg font-medium">{formatLabel(data)}</h2>
        {data.blocks.map((block, i) => {
          switch (block.type) {
            case "metrics-grid":
              return <MetricsGridBlockView key={i} block={block} />;
            case "area-chart":
              return <AreaChartBlockView key={i} block={block} />;
            case "horizontal-bar":
              return <HorizontalBarBlockView key={i} block={block} />;
            case "bar-chart":
              return <BarChartBlockView key={i} block={block} />;
            case "table":
              return <TableBlockView key={i} block={block} />;
          }
        })}
      </div>
    </div>
  );
}
