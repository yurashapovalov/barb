import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  createConversation,
  listConversations,
  deleteConversation,
  getMessages,
  sendMessage,
} from "./api";

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

describe("deleteConversation", () => {
  it("sends DELETE request", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));

    await deleteConversation("conv-1", "tok-123");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/conversations/conv-1"),
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("throws on error", async () => {
    mockFetch.mockResolvedValue(errorResponse(404, "Not found"));
    await expect(deleteConversation("bad", "tok")).rejects.toThrow("API error 404");
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

describe("sendMessage", () => {
  it("sends POST with conversation_id and message", async () => {
    const resp = {
      message_id: "m-1",
      conversation_id: "conv-1",
      answer: "The range is 150.",
      data: [],
      usage: { input_tokens: 100 },
      tool_calls: [],
      persisted: true,
    };
    mockFetch.mockResolvedValue(jsonResponse(resp));

    const result = await sendMessage("conv-1", "What is the range?", "tok-123");

    expect(result).toEqual(resp);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/chat"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          conversation_id: "conv-1",
          message: "What is the range?",
        }),
      }),
    );
  });

  it("throws on server error", async () => {
    mockFetch.mockResolvedValue(errorResponse(503, "Service unavailable"));
    await expect(sendMessage("c", "msg", "tok")).rejects.toThrow("API error 503");
  });
});
