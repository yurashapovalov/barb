import { Bar, BarChart as RechartsBarChart, Cell, XAxis, YAxis } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { formatColumnLabel, formatValue } from "@/lib/format";

const COLOR_POSITIVE = "oklch(0.65 0.2 145)"; // green
const COLOR_NEGATIVE = "oklch(0.65 0.2 25)";  // red

interface BarChartProps {
  data: Record<string, unknown>[];
  categoryKey: string;
  valueKey: string;
}

export function BarChart({ data, categoryKey, valueKey }: BarChartProps) {
  const valueLabel = formatColumnLabel(valueKey);

  const config: ChartConfig = {
    [valueKey]: { label: valueLabel },
    positive: { label: "Positive", color: COLOR_POSITIVE },
    negative: { label: "Negative", color: COLOR_NEGATIVE },
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
        <ChartTooltip
          content={
            <ChartTooltipContent
              formatter={(value) => formatValue(value, { decimals: 2 })}
            />
          }
        />
        <Bar dataKey={valueKey} radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => {
            const value = entry[valueKey];
            const isPositive = typeof value === "number" && value >= 0;
            return (
              <Cell
                key={index}
                fill={isPositive ? COLOR_POSITIVE : COLOR_NEGATIVE}
              />
            );
          })}
        </Bar>
      </RechartsBarChart>
    </ChartContainer>
  );
}
