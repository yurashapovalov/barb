import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useChat } from "./use-chat";
import * as api from "@/lib/api";
import type { Message, ChatResponse } from "@/types";

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

function makeChatResponse(overrides: Partial<ChatResponse> = {}): ChatResponse {
  return {
    message_id: "msg-resp-1",
    conversation_id: "conv-1",
    answer: "The range is 150.",
    data: [],
    usage: {
      input_tokens: 100, output_tokens: 50, thinking_tokens: 0,
      cached_tokens: 0, input_cost: 0, output_cost: 0,
      thinking_cost: 0, total_cost: 0,
    },
    tool_calls: [],
    persisted: true,
    ...overrides,
  };
}

beforeEach(() => {
  vi.resetAllMocks();
});

describe("useChat", () => {
  it("starts with empty messages when no conversationId", () => {
    const { result } = renderHook(() =>
      useChat({ conversationId: undefined, token: TOKEN }),
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
      useChat({ conversationId: "conv-1", token: TOKEN }),
    );

    await waitFor(() => {
      expect(result.current.messages).toEqual(msgs);
    });
    expect(mockedApi.getMessages).toHaveBeenCalledWith("conv-1", TOKEN);
  });

  it("sets error on history load failure", async () => {
    mockedApi.getMessages.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() =>
      useChat({ conversationId: "conv-1", token: TOKEN }),
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
    mockedApi.sendMessage.mockResolvedValue(makeChatResponse({
      conversation_id: "new-conv",
    }));

    const onCreated = vi.fn();

    const { result } = renderHook(() =>
      useChat({
        conversationId: undefined,
        token: TOKEN,
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

  it("sends message to existing conversation", async () => {
    mockedApi.getMessages.mockResolvedValue([]);
    mockedApi.sendMessage.mockResolvedValue(makeChatResponse());

    const { result } = renderHook(() =>
      useChat({ conversationId: "conv-1", token: TOKEN }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.send("What is the range?");
    });

    expect(mockedApi.createConversation).not.toHaveBeenCalled();
    expect(mockedApi.sendMessage).toHaveBeenCalledWith("conv-1", "What is the range?", TOKEN);
    expect(result.current.messages).toHaveLength(2);
  });

  it("removes optimistic message on send error", async () => {
    mockedApi.getMessages.mockResolvedValue([]);
    mockedApi.sendMessage.mockRejectedValue(new Error("Server down"));

    const { result } = renderHook(() =>
      useChat({ conversationId: "conv-1", token: TOKEN }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.send("hello");
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.error).toBe("Server down");
  });

  it("sets error when conversation creation fails", async () => {
    mockedApi.createConversation.mockRejectedValue(new Error("Auth failed"));

    const { result } = renderHook(() =>
      useChat({ conversationId: undefined, token: TOKEN }),
    );

    await act(async () => {
      await result.current.send("hello");
    });

    expect(result.current.error).toBe("Auth failed");
    expect(result.current.messages).toHaveLength(0);
    expect(mockedApi.sendMessage).not.toHaveBeenCalled();
  });
});
