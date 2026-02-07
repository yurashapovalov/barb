import { Bar, BarChart as RechartsBarChart, XAxis, YAxis } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";

interface BarChartProps {
  data: Record<string, unknown>[];
  categoryKey: string;
  valueKey: string;
}

export function BarChart({ data, categoryKey, valueKey }: BarChartProps) {
  const config: ChartConfig = {
    [valueKey]: {
      label: valueKey,
      color: "hsl(var(--chart-1))",
    },
  };

  return (
    <ChartContainer config={config} className="h-[200px] w-full">
      <RechartsBarChart data={data} margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
        <XAxis
          dataKey={categoryKey}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          width={50}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar
          dataKey={valueKey}
          fill={`var(--color-${valueKey})`}
          radius={[4, 4, 0, 0]}
        />
      </RechartsBarChart>
    </ChartContainer>
  );
}
