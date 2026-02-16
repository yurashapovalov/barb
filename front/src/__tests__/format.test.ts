import { describe, it, expect } from "vitest";
import { formatColumnLabel, formatValue } from "@/lib/format";

describe("formatColumnLabel", () => {
  it("returns known label for mapped keys", () => {
    expect(formatColumnLabel("date")).toBe("Date");
    expect(formatColumnLabel("open")).toBe("Open");
    expect(formatColumnLabel("volume")).toBe("Volume");
    expect(formatColumnLabel("dow")).toBe("Day of week");
  });

  it("converts snake_case to Title Case for unknown keys", () => {
    expect(formatColumnLabel("mean_gap")).toBe("Mean Gap");
    expect(formatColumnLabel("drop_pct")).toBe("Drop Pct");
  });

  it("handles single word", () => {
    expect(formatColumnLabel("custom")).toBe("Custom");
  });

  it("handles multiple underscores", () => {
    expect(formatColumnLabel("avg_daily_range")).toBe("Avg Daily Range");
  });
});

describe("formatValue", () => {
  it("returns dash for null", () => {
    expect(formatValue(null)).toBe("—");
  });

  it("returns dash for undefined", () => {
    expect(formatValue(undefined)).toBe("—");
  });

  it("formats integers without trailing decimals", () => {
    expect(formatValue(1234)).toBe("1,234");
  });

  it("formats decimals to 2 places by default", () => {
    expect(formatValue(1234.567)).toBe("1,234.57");
  });

  it("respects custom decimal places", () => {
    expect(formatValue(0.123456, { decimals: 4 })).toBe("0.1235");
  });

  it("formats zero", () => {
    expect(formatValue(0)).toBe("0");
  });

  it("formats negative numbers", () => {
    expect(formatValue(-42.5)).toBe("-42.5");
  });

  it("returns string as-is", () => {
    expect(formatValue("hello")).toBe("hello");
  });

  it("converts boolean to string", () => {
    expect(formatValue(true)).toBe("true");
  });
});
