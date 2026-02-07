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
import type { DataBlock } from "@/types";
import { PanelHeader } from "./panel-header";

type ChartInfo = {
  type: "bar" | "line" | null;
  categoryKey: string;
  valueKey: string;
} | null;

function detectChart(rows: Record<string, unknown>[]): ChartInfo {
  // Need 2-20 rows for a meaningful bar chart
  if (rows.length < 2 || rows.length > 20) return null;

  const firstRow = rows[0];
  const keys = Object.keys(firstRow);

  // Need at least 2 columns (category + value)
  if (keys.length < 2) return null;

  // Find category column (first non-numeric or small integer like weekday 0-6)
  // Find value column (numeric)
  let categoryKey: string | null = null;
  let valueKey: string | null = null;

  for (const key of keys) {
    const value = firstRow[key];
    const isNumeric = typeof value === "number";

    if (!categoryKey && !isNumeric) {
      categoryKey = key;
    } else if (!categoryKey && isNumeric && Number.isInteger(value) && (value as number) >= 0 && (value as number) <= 12) {
      // Small integers (0-12) could be weekday/month - treat as category
      categoryKey = key;
    } else if (!valueKey && isNumeric) {
      valueKey = key;
    }
  }

  // If no category found, use first column
  if (!categoryKey && keys.length >= 2) {
    categoryKey = keys[0];
  }

  if (!categoryKey || !valueKey) return null;

  return { type: "bar", categoryKey, valueKey };
}

type Row = Record<string, unknown>;

function normalizeResult(result: unknown): Row[] {
  if (Array.isArray(result)) return result as Row[];
  if (result !== null && typeof result === "object") return [result as Row];
  return [{ value: result }];
}

function buildColumns(rows: Row[]): ColumnDef<Row>[] {
  if (rows.length === 0) return [];
  return Object.keys(rows[0]).map((key) => ({
    accessorKey: key,
    header: ({ column }) => {
      const sorted = column.getIsSorted();
      return (
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-1 outline-none">
            {key}
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
  const columns = buildColumns(rows);
  const chartInfo = detectChart(rows);

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
        <Button variant="ghost" size="icon-sm" onClick={onClose}>
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
