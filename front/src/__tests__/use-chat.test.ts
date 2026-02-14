import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useChat } from "@/hooks/use-chat";
import * as api from "@/lib/api";
import type { Message } from "@/types";

vi.mock("@/lib/api");

const mockedApi = vi.mocked(api);

const TOKEN = "test-token";

function makeMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: "msg-1",
    conversation_id: "conv-1",
    role: "user",
    content: "hello",
    data: null,
    usage: null,
    created_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

/** Simulate sendMessageStream: calls onDone and onPersist synchronously. */
function mockStreamSuccess(answer = "The range is 150.") {
  mockedApi.sendMessageStream.mockImplementation(
    async (_convId, _msg, _token, callbacks) => {
      callbacks.onTextDelta?.({ delta: answer });
      callbacks.onDone?.({
        answer,
        usage: {
          input_tokens: 100, output_tokens: 50, thinking_tokens: 0,
          cached_tokens: 0, input_cost: 0, output_cost: 0,
          thinking_cost: 0, total_cost: 0,
        },
        tool_calls: [],
        data: [],
      });
      callbacks.onPersist?.({ message_id: "msg-resp-1", persisted: true });
    },
  );
}

beforeEach(() => {
  vi.resetAllMocks();
});

describe("useChat", () => {
  it("starts with empty messages when no conversationId", () => {
    const { result } = renderHook(() =>
      useChat({ conversationId: undefined, token: TOKEN, instrument: "NQ" }),
    );

    expect(result.current.messages).toEqual([]);
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("loads history when conversationId is provided", async () => {
    const msgs = [
      makeMessage({ id: "m1", role: "user", content: "hi" }),
      makeMessage({ id: "m2", role: "model", content: "hello" }),
    ];
    mockedApi.getMessages.mockResolvedValue(msgs);

    const { result } = renderHook(() =>
      useChat({ conversationId: "conv-1", token: TOKEN, instrument: "NQ" }),
    );

    await waitFor(() => {
      expect(result.current.messages).toEqual(msgs);
    });
    expect(mockedApi.getMessages).toHaveBeenCalledWith("conv-1", TOKEN);
  });

  it("sets error on history load failure", async () => {
    mockedApi.getMessages.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() =>
      useChat({ conversationId: "conv-err", token: TOKEN, instrument: "NQ" }),
    );

    await waitFor(() => {
      expect(result.current.error).toBe("Network error");
    });
  });

  it("creates conversation on first send when no conversationId", async () => {
    mockedApi.createConversation.mockResolvedValue({
      id: "new-conv",
      title: "New conversation",
      instrument: "NQ",
      usage: {
        input_tokens: 0, output_tokens: 0, thinking_tokens: 0,
        cached_tokens: 0, input_cost: 0, output_cost: 0,
        thinking_cost: 0, total_cost: 0, message_count: 0,
      },
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    });
    mockStreamSuccess();

    const onCreated = vi.fn();

    const { result } = renderHook(() =>
      useChat({
        conversationId: undefined,
        token: TOKEN,
        instrument: "NQ",
        onConversationCreated: onCreated,
      }),
    );

    await act(async () => {
      await result.current.send("hello");
    });

    expect(mockedApi.createConversation).toHaveBeenCalledWith("NQ", TOKEN);
    expect(onCreated).toHaveBeenCalledWith("new-conv");
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[1].role).toBe("model");
  });

  it("sends message to existing conversation via stream", async () => {
    mockedApi.getMessages.mockResolvedValue([]);
    mockStreamSuccess();

    const { result } = renderHook(() =>
      useChat({ conversationId: "conv-send", token: TOKEN, instrument: "NQ" }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.send("What is the range?");
    });

    expect(mockedApi.createConversation).not.toHaveBeenCalled();
    expect(mockedApi.sendMessageStream).toHaveBeenCalledWith(
      "conv-send", "What is the range?", TOKEN,
      expect.any(Object), expect.any(AbortSignal),
    );
    // user + assistant placeholder
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].content).toBe("The range is 150.");
    expect(result.current.messages[1].id).toBe("msg-resp-1");
  });

  it("removes optimistic messages on stream error", async () => {
    mockedApi.getMessages.mockResolvedValue([]);
    mockedApi.sendMessageStream.mockRejectedValue(new Error("Server down"));

    const { result } = renderHook(() =>
      useChat({ conversationId: "conv-stream-err", token: TOKEN, instrument: "NQ" }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.send("hello").catch(() => {});
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.error).toBe("Server down");
  });

  it("sets error from SSE error event", async () => {
    mockedApi.getMessages.mockResolvedValue([]);
    mockedApi.sendMessageStream.mockImplementation(
      async (_convId, _msg, _token, callbacks) => {
        callbacks.onTextDelta?.({ delta: "partial" });
        callbacks.onError?.({ error: "Service temporarily unavailable" });
      },
    );

    const { result } = renderHook(() =>
      useChat({ conversationId: "conv-sse-err", token: TOKEN, instrument: "NQ" }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.send("hello");
    });

    expect(result.current.error).toBe("Service temporarily unavailable");
  });

  it("sets error when conversation creation fails", async () => {
    mockedApi.createConversation.mockRejectedValue(new Error("Auth failed"));

    const { result } = renderHook(() =>
      useChat({ conversationId: undefined, token: TOKEN, instrument: "NQ" }),
    );

    await act(async () => {
      await result.current.send("hello").catch(() => {});
    });

    expect(result.current.error).toBe("Auth failed");
    expect(result.current.messages).toHaveLength(0);
    expect(mockedApi.sendMessageStream).not.toHaveBeenCalled();
  });
});
