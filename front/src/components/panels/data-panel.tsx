import { useEffect, useState } from "react";
import {
  type ColumnDef,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowDownIcon, ArrowUpIcon, XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
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
import { formatColumnLabel } from "@/lib/format";
import type { DataBlock } from "@/types";
import { PanelHeader } from "./panel-header";

type ChartInfo = {
  type: "bar";
  categoryKey: string;
  valueKey: string;
} | null;

function getChartInfo(data: DataBlock, rows: Record<string, unknown>[]): ChartInfo {
  // Use chart hint from backend if available
  const hint = data.chart as { category?: string; value?: string } | undefined;
  if (hint?.category && hint?.value) {
    // Verify columns exist in data
    if (rows.length > 0 && hint.category in rows[0] && hint.value in rows[0]) {
      return { type: "bar", categoryKey: hint.category, valueKey: hint.value };
    }
  }

  // No chart hint - don't show chart
  return null;
}

type Row = Record<string, unknown>;

function normalizeResult(result: unknown): Row[] {
  if (Array.isArray(result)) return result as Row[];
  if (result !== null && typeof result === "object") return [result as Row];
  return [{ value: result }];
}

function buildColumns(rows: Row[], columnOrder?: string[] | null): ColumnDef<Row>[] {
  if (rows.length === 0) return [];
  const keys = columnOrder ?? Object.keys(rows[0]);
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

interface DataPanelProps {
  data: DataBlock;
  onClose: () => void;
}

export function DataPanel({ data, onClose }: DataPanelProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  useEffect(() => {
    setSorting([]);
  }, [data]);

  const rows = normalizeResult(data.source_rows ?? data.result);
  const columns = buildColumns(rows, data.columns);
  const chartInfo = getChartInfo(data, rows);

  const table = useReactTable({
    data: rows,
    columns,
    getCoreRowModel: coreRowModel,
    getSortedRowModel: sortedRowModel,
    onSortingChange: setSorting,
    state: { sorting },
  });

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
        {chartInfo?.type === "bar" && (
          <div className="px-6 pb-4">
            <BarChart
              data={rows}
              categoryKey={chartInfo.categoryKey}
              valueKey={chartInfo.valueKey}
            />
          </div>
        )}
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
      </div>
    </div>
  );
}
