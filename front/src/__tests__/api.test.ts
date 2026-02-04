import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  createConversation,
  listConversations,
  removeConversation,
  getMessages,
  sendMessageStream,
} from "@/lib/api";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function errorResponse(status: number, body: string) {
  return new Response(body, { status });
}

/** Build a ReadableStream that emits SSE events. */
function sseResponse(events: Array<{ event: string; data: unknown }>) {
  const body = events
    .map((e) => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`)
    .join("");
  return new Response(body, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe("createConversation", () => {
  it("sends POST with instrument and token", async () => {
    const conv = { id: "conv-1", title: "New conversation", instrument: "NQ" };
    mockFetch.mockResolvedValue(jsonResponse(conv));

    const result = await createConversation("NQ", "tok-123");

    expect(result).toEqual(conv);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/conversations"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ Authorization: "Bearer tok-123" }),
        body: JSON.stringify({ instrument: "NQ" }),
      }),
    );
  });

  it("throws on error response", async () => {
    mockFetch.mockResolvedValue(errorResponse(400, "Bad request"));
    await expect(createConversation("BAD", "tok")).rejects.toThrow("API error 400");
  });
});

describe("listConversations", () => {
  it("returns conversation list", async () => {
    const convs = [{ id: "conv-1" }, { id: "conv-2" }];
    mockFetch.mockResolvedValue(jsonResponse(convs));

    const result = await listConversations("tok-123");

    expect(result).toEqual(convs);
  });
});

describe("removeConversation", () => {
  it("sends DELETE request", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));

    await removeConversation("conv-1", "tok-123");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/conversations/conv-1"),
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("throws on error", async () => {
    mockFetch.mockResolvedValue(errorResponse(404, "Not found"));
    await expect(removeConversation("bad", "tok")).rejects.toThrow("API error 404");
  });
});

describe("getMessages", () => {
  it("returns messages for conversation", async () => {
    const msgs = [
      { id: "m1", role: "user", content: "hello" },
      { id: "m2", role: "model", content: "hi" },
    ];
    mockFetch.mockResolvedValue(jsonResponse(msgs));

    const result = await getMessages("conv-1", "tok-123");

    expect(result).toEqual(msgs);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/conversations/conv-1/messages"),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer tok-123" }),
      }),
    );
  });
});

describe("sendMessageStream", () => {
  it("dispatches SSE events to callbacks", async () => {
    mockFetch.mockResolvedValue(
      sseResponse([
        { event: "tool_start", data: { tool_name: "execute_query", input: {} } },
        { event: "tool_end", data: { tool_name: "execute_query", duration_ms: 10, error: null } },
        { event: "text_delta", data: { delta: "Result is 42." } },
        { event: "done", data: { answer: "Result is 42.", usage: {}, tool_calls: [], data: [] } },
        { event: "persist", data: { message_id: "m-1", persisted: true } },
      ]),
    );

    const onToolStart = vi.fn();
    const onToolEnd = vi.fn();
    const onTextDelta = vi.fn();
    const onDone = vi.fn();
    const onPersist = vi.fn();

    await sendMessageStream("conv-1", "query", "tok-123", {
      onToolStart,
      onToolEnd,
      onTextDelta,
      onDone,
      onPersist,
    });

    expect(onToolStart).toHaveBeenCalledWith({ tool_name: "execute_query", input: {} });
    expect(onToolEnd).toHaveBeenCalledWith({ tool_name: "execute_query", duration_ms: 10, error: null });
    expect(onTextDelta).toHaveBeenCalledWith({ delta: "Result is 42." });
    expect(onDone).toHaveBeenCalledWith(
      expect.objectContaining({ answer: "Result is 42." }),
    );
    expect(onPersist).toHaveBeenCalledWith({ message_id: "m-1", persisted: true });
  });

  it("throws on HTTP error before stream starts", async () => {
    mockFetch.mockResolvedValue(errorResponse(503, "Service unavailable"));
    await expect(
      sendMessageStream("c", "msg", "tok", {}),
    ).rejects.toThrow("API error 503");
  });

  it("dispatches data_block events", async () => {
    const block = { query: { select: "range" }, result: 150, rows: 1, session: "RTH", timeframe: null };
    mockFetch.mockResolvedValue(
      sseResponse([
        { event: "data_block", data: block },
        { event: "done", data: { answer: "", usage: {}, tool_calls: [], data: [block] } },
      ]),
    );

    const onDataBlock = vi.fn();
    const onDone = vi.fn();
    await sendMessageStream("conv-1", "query", "tok-123", { onDataBlock, onDone });

    expect(onDataBlock).toHaveBeenCalledWith(block);
    expect(onDone).toHaveBeenCalled();
  });

  it("skips malformed JSON in SSE stream without crashing", async () => {
    // Build a response with one malformed event followed by a valid one
    const body =
      `event: text_delta\ndata: {INVALID JSON}\n\n` +
      `event: done\ndata: ${JSON.stringify({ answer: "ok", usage: {}, tool_calls: [], data: [] })}\n\n`;
    mockFetch.mockResolvedValue(
      new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } }),
    );

    const onTextDelta = vi.fn();
    const onDone = vi.fn();
    await sendMessageStream("conv-1", "query", "tok-123", { onTextDelta, onDone });

    // Malformed event skipped, valid event still dispatched
    expect(onTextDelta).not.toHaveBeenCalled();
    expect(onDone).toHaveBeenCalledWith(expect.objectContaining({ answer: "ok" }));
  });

  it("dispatches error events from stream", async () => {
    mockFetch.mockResolvedValue(
      sseResponse([
        { event: "error", data: { error: "Service temporarily unavailable" } },
      ]),
    );

    const onError = vi.fn();
    await sendMessageStream("conv-1", "query", "tok", { onError });

    expect(onError).toHaveBeenCalledWith({ error: "Service temporarily unavailable" });
  });

  it("skips text_delta without delta field", async () => {
    mockFetch.mockResolvedValue(
      sseResponse([
        { event: "text_delta", data: { wrong_field: "oops" } },
        { event: "text_delta", data: { delta: "valid" } },
      ]),
    );

    const onTextDelta = vi.fn();
    await sendMessageStream("conv-1", "q", "tok", { onTextDelta });

    expect(onTextDelta).toHaveBeenCalledTimes(1);
    expect(onTextDelta).toHaveBeenCalledWith({ delta: "valid" });
  });

  it("skips done without answer field", async () => {
    mockFetch.mockResolvedValue(
      sseResponse([
        { event: "done", data: { no_answer: true } },
      ]),
    );

    const onDone = vi.fn();
    await sendMessageStream("conv-1", "q", "tok", { onDone });

    expect(onDone).not.toHaveBeenCalled();
  });

  it("skips tool_start without tool_name field", async () => {
    mockFetch.mockResolvedValue(
      sseResponse([
        { event: "tool_start", data: { input: {} } },
        { event: "tool_start", data: { tool_name: "query", input: {} } },
      ]),
    );

    const onToolStart = vi.fn();
    await sendMessageStream("conv-1", "q", "tok", { onToolStart });

    expect(onToolStart).toHaveBeenCalledTimes(1);
    expect(onToolStart).toHaveBeenCalledWith({ tool_name: "query", input: {} });
  });

  it("skips error event without error field", async () => {
    mockFetch.mockResolvedValue(
      sseResponse([
        { event: "error", data: { message: "bad" } },
      ]),
    );

    const onError = vi.fn();
    await sendMessageStream("conv-1", "q", "tok", { onError });

    expect(onError).not.toHaveBeenCalled();
  });
});
