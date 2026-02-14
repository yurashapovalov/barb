import { useEffect, useRef } from "react";
import { createChart, ColorType, CandlestickSeries, HistogramSeries, type IChartApi, type ISeriesApi } from "lightweight-charts";
import type { OHLCBar } from "@/lib/api";

interface CandlestickChartProps {
  data: OHLCBar[];
}

function isDark() {
  return document.documentElement.classList.contains("dark");
}

// Hardcoded hex values — lightweight-charts doesn't support CSS variables (oklch).
// These match Tailwind's zinc palette. Update both if design system changes.
function getTheme(dark: boolean) {
  return {
    layout: {
      background: { type: ColorType.Solid as const, color: dark ? "#09090b" : "#ffffff" },
      textColor: dark ? "#a1a1aa" : "#71717a",
    },
    grid: {
      vertLines: { color: dark ? "#27272a" : "#f4f4f5" },
      horzLines: { color: dark ? "#27272a" : "#f4f4f5" },
    },
    crosshair: {
      vertLine: { labelBackgroundColor: dark ? "#27272a" : "#e4e4e7" },
      horzLine: { labelBackgroundColor: dark ? "#27272a" : "#e4e4e7" },
    },
    rightPriceScale: {
      borderColor: dark ? "#27272a" : "#e4e4e7",
    },
    timeScale: {
      borderColor: dark ? "#27272a" : "#e4e4e7",
    },
  };
}

export function CandlestickChart({ data }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  // Create chart once
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      ...getTheme(isDark()),
      width: container.clientWidth,
      height: container.clientHeight,
      handleScroll: true,
      handleScale: true,
    });
    chartRef.current = chart;

    candleSeriesRef.current = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderDownColor: "#ef5350",
      borderUpColor: "#26a69a",
      wickDownColor: "#ef5350",
      wickUpColor: "#26a69a",
    });

    volumeSeriesRef.current = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      chart.applyOptions({ width, height });
    });
    ro.observe(container);

    const mo = new MutationObserver(() => {
      chart.applyOptions(getTheme(isDark()));
    });
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    return () => {
      mo.disconnect();
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  // Update data without recreating chart
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || !chartRef.current) return;

    const candleData = data.map((bar) => ({
      time: bar.time,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));

    const volumeData = data.map((bar) => ({
      time: bar.time,
      value: bar.volume,
      color: bar.close >= bar.open
        ? "rgba(38, 166, 154, 0.3)"
        : "rgba(239, 83, 80, 0.3)",
    }));

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);

    // Show last ~2 months by default
    if (candleData.length > 60) {
      chartRef.current.timeScale().setVisibleLogicalRange({
        from: candleData.length - 60,
        to: candleData.length - 1,
      });
    } else {
      chartRef.current.timeScale().fitContent();
    }
  }, [data]);

  return <div ref={containerRef} className="h-[400px] w-full" />;
}
