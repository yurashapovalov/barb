/**
 * Formatting utilities for display values.
 *
 * Backend sends raw column names (snake_case).
 * Frontend formats them for display.
 */

// Known column labels
const COLUMN_LABELS: Record<string, string> = {
  // Time
  date: "Date",
  time: "Time",
  // OHLCV
  open: "Open",
  high: "High",
  low: "Low",
  close: "Close",
  volume: "Volume",
  // Common aggregates
  count: "Count",
  // Common calculated
  dow: "Day of week",
  gap: "Gap",
  range: "Range",
};

/**
 * Format column key for display.
 *
 * @example
 * formatColumnLabel("date") // "Date"
 * formatColumnLabel("mean_gap") // "Mean Gap"
 * formatColumnLabel("drop_pct") // "Drop Pct"
 */
export function formatColumnLabel(key: string): string {
  if (key in COLUMN_LABELS) return COLUMN_LABELS[key];

  // Transform snake_case to Title Case
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Format value for display.
 *
 * @example
 * formatValue(null) // "—"
 * formatValue(1234.567) // "1,234.57"
 * formatValue(0.123456, { decimals: 4 }) // "0.1235"
 */
export function formatValue(
  value: unknown,
  options?: { decimals?: number }
): string {
  if (value === null || value === undefined) return "—";

  if (typeof value === "number") {
    const decimals = options?.decimals ?? 2;
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: decimals,
    });
  }

  return String(value);
}
