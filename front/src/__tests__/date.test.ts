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

  it("returns Just now for less than a minute ago", () => {
    freeze("2026-02-16T12:00:30");
    expect(formatRelativeDate("2026-02-16T12:00:00")).toBe("Just now");
  });

  it("returns minutes ago", () => {
    freeze("2026-02-16T12:05:00");
    expect(formatRelativeDate("2026-02-16T12:00:00")).toBe("5 min ago");
  });

  it("returns 1 hour ago (singular)", () => {
    freeze("2026-02-16T13:00:00");
    expect(formatRelativeDate("2026-02-16T12:00:00")).toBe("1 hour ago");
  });

  it("returns hours ago (plural)", () => {
    freeze("2026-02-16T15:00:00");
    expect(formatRelativeDate("2026-02-16T12:00:00")).toBe("3 hours ago");
  });

  it("returns date with time for yesterday", () => {
    freeze("2026-02-16T12:00:00");
    const result = formatRelativeDate("2026-02-15T16:10:00");
    expect(result).toContain("15");
    expect(result).toMatch(/16:10|4:10/);
  });

  it("returns date with time for same year", () => {
    freeze("2026-02-16T12:00:00");
    const result = formatRelativeDate("2026-01-05T09:30:00");
    expect(result).toContain("5");
    expect(result).toMatch(/9:30/);
  });

  it("includes year for different year", () => {
    freeze("2026-02-16T12:00:00");
    const result = formatRelativeDate("2025-12-25T14:00:00");
    expect(result).toContain("25");
    expect(result).toContain("2025");
  });

  it("handles year boundary", () => {
    freeze("2026-01-01T12:00:00");
    const result = formatRelativeDate("2025-12-31T20:00:00");
    expect(result).toContain("31");
    expect(result).toContain("2025");
  });

  it("returns Just now for future date on same day (clock skew)", () => {
    freeze("2026-02-16T12:00:00");
    expect(formatRelativeDate("2026-02-16T12:05:00")).toBe("Just now");
  });

  it("returns input string for invalid date", () => {
    expect(formatRelativeDate("not-a-date")).toBe("not-a-date");
  });
});
