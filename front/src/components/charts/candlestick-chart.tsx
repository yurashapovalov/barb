import { useEffect, useRef } from "react";
import { createChart, ColorType, CandlestickSeries, HistogramSeries, type IChartApi } from "lightweight-charts";
import type { OHLCBar } from "@/lib/api";

interface CandlestickChartProps {
  data: OHLCBar[];
}

function isDark() {
  return document.documentElement.classList.contains("dark");
}

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

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const dark = isDark();
    const chart = createChart(container, {
      ...getTheme(dark),
      width: container.clientWidth,
      height: container.clientHeight,
      handleScroll: true,
      handleScale: true,
    });
    chartRef.current = chart;

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderDownColor: "#ef5350",
      borderUpColor: "#26a69a",
      wickDownColor: "#ef5350",
      wickUpColor: "#26a69a",
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });

    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

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

    candlestickSeries.setData(candleData);
    volumeSeries.setData(volumeData);

    // Show last ~2 months by default
    if (candleData.length > 60) {
      chart.timeScale().setVisibleLogicalRange({
        from: candleData.length - 60,
        to: candleData.length - 1,
      });
    } else {
      chart.timeScale().fitContent();
    }

    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      chart.applyOptions({ width, height });
    });
    ro.observe(container);

    // Theme observer — watch for class changes on <html>
    const mo = new MutationObserver(() => {
      chart.applyOptions(getTheme(isDark()));
    });
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    return () => {
      mo.disconnect();
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [data]);

  return <div ref={containerRef} className="h-[400px] w-full" />;
}
