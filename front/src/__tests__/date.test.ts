import { describe, it, expect, vi, afterEach } from "vitest";
import { formatRelativeDate } from "@/lib/date";

describe("formatRelativeDate", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  function freeze(dateStr: string) {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(dateStr));
  }

  it("returns Today for current date", () => {
    freeze("2026-02-16T12:00:00");
    expect(formatRelativeDate("2026-02-16T09:30:00")).toBe("Today");
  });

  it("returns Today regardless of time", () => {
    freeze("2026-02-16T23:59:00");
    expect(formatRelativeDate("2026-02-16T00:01:00")).toBe("Today");
  });

  it("returns Yesterday for previous date", () => {
    freeze("2026-02-16T12:00:00");
    expect(formatRelativeDate("2026-02-15T20:00:00")).toBe("Yesterday");
  });

  it("returns short date for same year", () => {
    freeze("2026-02-16T12:00:00");
    expect(formatRelativeDate("2026-02-10T12:00:00")).toBe("Feb 10");
  });

  it("returns short date with year for different year", () => {
    freeze("2026-02-16T12:00:00");
    expect(formatRelativeDate("2025-12-25T12:00:00")).toBe("Dec 25, 2025");
  });

  it("returns short date for 2 days ago (not Yesterday)", () => {
    freeze("2026-02-16T12:00:00");
    expect(formatRelativeDate("2026-02-14T12:00:00")).toBe("Feb 14");
  });

  it("handles Jan 1 looking back to previous year", () => {
    freeze("2026-01-01T12:00:00");
    expect(formatRelativeDate("2025-12-31T12:00:00")).toBe("Yesterday");
  });

  it("handles Jan 1 with date from previous year beyond yesterday", () => {
    freeze("2026-01-01T12:00:00");
    expect(formatRelativeDate("2025-12-30T12:00:00")).toBe("Dec 30, 2025");
  });
});
