import { describe, it, expect } from "vitest";
import { parseContent } from "@/lib/parse-content";
import type { Message } from "@/types";
import type { DataBlock } from "@/types";

function msg(content: string, data: DataBlock[] | null = null): Message {
  return {
    id: "m1",
    conversation_id: "c1",
    role: "model",
    content,
    data,
    usage: null,
    created_at: "2024-01-01T00:00:00Z",
  };
}

const block0: DataBlock = { query: {}, result: 42, session: "RTH", timeframe: "daily" } as DataBlock;
const block1: DataBlock = { query: {}, result: 100, session: "ETH", timeframe: "weekly" } as DataBlock;

describe("parseContent", () => {
  it("returns single text segment when no data", () => {
    const result = parseContent(msg("Hello world"));
    expect(result).toEqual([{ type: "text", text: "Hello world" }]);
  });

  it("returns single text segment when data is null", () => {
    const result = parseContent(msg("Hello", null));
    expect(result).toEqual([{ type: "text", text: "Hello" }]);
  });

  it("returns single text segment when data is empty array", () => {
    const result = parseContent(msg("Hello", []));
    expect(result).toEqual([{ type: "text", text: "Hello" }]);
  });

  it("splits text around a single marker", () => {
    const result = parseContent(msg("Before\n\n{{data:0}}\n\nAfter", [block0]));
    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({ type: "text", text: expect.stringContaining("Before") });
    expect(result[1]).toEqual({ type: "data", block: block0, index: 0 });
    expect(result[2]).toEqual({ type: "text", text: expect.stringContaining("After") });
  });

  it("handles marker at the start", () => {
    const result = parseContent(msg("{{data:0}}\n\nAfter", [block0]));
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ type: "data", block: block0, index: 0 });
    expect(result[1]).toEqual({ type: "text", text: expect.stringContaining("After") });
  });

  it("handles marker at the end", () => {
    const result = parseContent(msg("Before\n\n{{data:0}}", [block0]));
    expect(result).toHaveLength(2);
    expect(result[0]).toEqual({ type: "text", text: expect.stringContaining("Before") });
    expect(result[1]).toEqual({ type: "data", block: block0, index: 0 });
  });

  it("handles multiple markers", () => {
    const result = parseContent(msg(
      "Intro\n\n{{data:0}}\n\nMiddle\n\n{{data:1}}\n\nEnd",
      [block0, block1],
    ));
    expect(result).toHaveLength(5);
    expect(result[0].type).toBe("text");
    expect(result[1]).toEqual({ type: "data", block: block0, index: 0 });
    expect(result[2].type).toBe("text");
    expect(result[3]).toEqual({ type: "data", block: block1, index: 1 });
    expect(result[4].type).toBe("text");
  });

  it("handles consecutive markers with no text between", () => {
    const result = parseContent(msg("{{data:0}}\n\n{{data:1}}", [block0, block1]));
    const dataSegments = result.filter((s) => s.type === "data");
    expect(dataSegments).toHaveLength(2);
  });

  it("skips marker with out-of-bounds index", () => {
    const result = parseContent(msg("Before\n\n{{data:5}}\n\nAfter", [block0]));
    // data:5 doesn't exist — no data segments from markers, falls back to end
    const dataSegments = result.filter((s) => s.type === "data");
    expect(dataSegments).toHaveLength(1);
    expect(dataSegments[0]).toEqual({ type: "data", block: block0, index: 0 });
  });

  it("falls back to cards at end for historical messages without markers", () => {
    const result = parseContent(msg("Some analysis text", [block0, block1]));
    expect(result).toEqual([
      { type: "text", text: "Some analysis text" },
      { type: "data", block: block0, index: 0 },
      { type: "data", block: block1, index: 1 },
    ]);
  });

  it("ignores whitespace-only text between markers", () => {
    const result = parseContent(msg("Text\n\n{{data:0}}\n\n   \n\n{{data:1}}", [block0, block1]));
    const dataSegments = result.filter((s) => s.type === "data");
    expect(dataSegments).toHaveLength(2);
    // First segment is text containing "Text"
    expect(result[0]).toEqual({ type: "text", text: expect.stringContaining("Text") });
  });
});
