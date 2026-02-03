import type { DataBlock, Message } from "@/types";

export type ContentSegment =
  | { type: "text"; text: string }
  | { type: "data"; block: DataBlock; index: number };

const DATA_MARKER = /\{\{data:(\d+)\}\}/g;

export function parseContent(msg: Message): ContentSegment[] {
  if (!msg.data?.length) {
    return [{ type: "text", text: msg.content }];
  }

  const segments: ContentSegment[] = [];
  let lastIndex = 0;

  for (const match of msg.content.matchAll(DATA_MARKER)) {
    const before = msg.content.slice(lastIndex, match.index);
    if (before.trim()) segments.push({ type: "text", text: before });
    const blockIndex = Number(match[1]);
    if (msg.data[blockIndex]) {
      segments.push({ type: "data", block: msg.data[blockIndex], index: blockIndex });
    }
    lastIndex = match.index + match[0].length;
  }

  const after = msg.content.slice(lastIndex);
  if (after.trim()) segments.push({ type: "text", text: after });

  // No markers found — cards at the end (historical messages from API)
  const hasData = segments.some((s) => s.type === "data");
  if (!hasData) {
    for (let i = 0; i < msg.data.length; i++) {
      segments.push({ type: "data" as const, block: msg.data[i], index: i });
    }
  }

  return segments;
}
