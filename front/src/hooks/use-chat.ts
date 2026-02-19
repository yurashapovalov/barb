import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { createConversation, getMessages, runBacktest, sendContinueStream, sendMessageStream } from "@/lib/api";
import type { DataBlock, Message } from "@/types";

export interface PendingTool {
  toolUseId: string;
  input: Record<string, unknown>;
  messageId: string;
  fullText: string;
  dataBlocks: DataBlock[];
}

interface UseChatParams {
  conversationId: string | undefined;
  token: string;
  instrument: string;
  onConversationCreated?: (id: string) => void;
  onTitleUpdate?: (id: string, title: string) => void;
}

export type ChatState = ReturnType<typeof useChat>;

// Module-level cache — survives component unmount/remount
const messageCache = new Map<string, Message[]>();
const MAX_CACHE = 10;

function cacheSet(key: string, value: Message[]) {
  messageCache.delete(key); // move to end (most recent)
  messageCache.set(key, value);
  if (messageCache.size > MAX_CACHE) {
    const oldest = messageCache.keys().next().value!;
    messageCache.delete(oldest);
  }
}

export function useChat({ conversationId, token, instrument, onConversationCreated, onTitleUpdate }: UseChatParams) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(() => !!conversationId);
  const [error, setError] = useState<string | null>(null);
  const [pendingTool, setPendingTool] = useState<PendingTool | null>(null);

  // Track current conversation ID (may change after creation)
  const convIdRef = useRef(conversationId);
  convIdRef.current = conversationId;

  // Skip loading when send() is in progress (it manages messages itself).
  // Unlike skipLoadRef, this survives StrictMode double-effect runs.
  const isSendingRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Don't touch messages while send() is in progress
    if (isSendingRef.current) return;

    if (!conversationId) {
      setMessages([]);
      setError(null);
      return;
    }

    const cached = messageCache.get(conversationId);
    if (cached) {
      setMessages(cached);
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getMessages(conversationId, token)
      .then((data) => {
        if (!cancelled) {
          setMessages(data);
          cacheSet(conversationId, data);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          toast.error(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
      abortRef.current?.abort();
    };
  }, [conversationId, token]);

  const send = async (text: string) => {
    isSendingRef.current = true;
    setError(null);

    // Show user message immediately — before any network calls
    const tempConvId = convIdRef.current ?? "pending";
    const userMsg: Message = {
      id: crypto.randomUUID(),
      conversation_id: tempConvId,
      role: "user",
      content: text,
      data: null,
      usage: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    let resolvedConvId = convIdRef.current;

    // Create conversation if needed
    if (!resolvedConvId) {
      try {
        const conv = await createConversation(instrument, token);
        resolvedConvId = conv.id;
        convIdRef.current = conv.id;
        try { onConversationCreated?.(conv.id); } catch { /* navigate may throw */ }
      } catch (err) {
        isSendingRef.current = false;
        const msg = err instanceof Error ? err.message : "Failed to create conversation";
        setError(msg);
        toast.error(msg);
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
        setIsLoading(false);
        throw err;
      }
    }

    // After the block above, resolvedConvId is always set (or we returned early)
    const activeConvId = resolvedConvId;

    const assistantId = crypto.randomUUID();
    let assistantAdded = false;

    const addAssistantMessage = () => {
      if (assistantAdded) return;
      assistantAdded = true;
      setMessages((prev) => [...prev, {
        id: assistantId,
        conversation_id: activeConvId,
        role: "model" as const,
        content: "",
        data: null,
        usage: null,
        created_at: new Date().toISOString(),
      }]);
    };

    let fullText = "";
    const dataBlocks: DataBlock[] = [];

    const abort = new AbortController();
    abortRef.current = abort;

    let loadingBlockIndex = -1;

    try {
      await sendMessageStream(activeConvId, text, token, {
        onTextDelta(event) {
          addAssistantMessage();
          fullText += event.delta;
          const content = fullText;
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content } : m)),
          );
        },
        onToolStart() {
          addAssistantMessage();
          const loadingBlock: DataBlock = {
            title: "Loading...",
            blocks: [],
            status: "loading",
          };
          dataBlocks.push(loadingBlock);
          loadingBlockIndex = dataBlocks.length - 1;
          fullText += `\n\n{{data:${loadingBlockIndex}}}\n\n`;
          const content = fullText;
          const data = [...dataBlocks];
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content, data } : m)),
          );
        },
        onToolEnd(event) {
          if (event.error && loadingBlockIndex >= 0) {
            dataBlocks[loadingBlockIndex] = {
              title: "Error",
              blocks: [],
              status: "error",
              error: event.error,
            };
            const data = [...dataBlocks];
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, data } : m)),
            );
          }
        },
        onToolPending(event) {
          addAssistantMessage();
          setPendingTool({
            toolUseId: event.tool_use_id,
            input: event.input,
            messageId: assistantId,
            fullText,
            dataBlocks: [...dataBlocks],
          });
        },
        onDataBlock(event) {
          addAssistantMessage();
          if (loadingBlockIndex >= 0) {
            // Replace loading block with real data
            dataBlocks[loadingBlockIndex] = { ...event, status: "success" as const };
            loadingBlockIndex = -1;
          } else {
            // No loading block, add new
            dataBlocks.push({ ...event, status: "success" as const });
            fullText += `\n\n{{data:${dataBlocks.length - 1}}}\n\n`;
          }
          const content = fullText;
          const data = [...dataBlocks];
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content, data } : m)),
          );
        },
        onDone(event) {
          setMessages((prev) => {
            const updated = prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    // Keep fullText with markers for inline data cards.
                    // Only use event.answer if we have no data blocks.
                    content: dataBlocks.length > 0 ? fullText : event.answer,
                    usage: event.usage,
                    // Use local dataBlocks (has status field) over event.data
                    data: dataBlocks.length > 0 ? dataBlocks : null,
                  }
                : m,
            );
            cacheSet(activeConvId, updated);
            return updated;
          });
        },
        onPersist(event) {
          if (event.message_id) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, id: event.message_id } : m,
              ),
            );
          }
        },
        onTitleUpdate(event) {
          onTitleUpdate?.(activeConvId, event.title);
        },
        onError(event) {
          setError(event.error);
          toast.error(event.error);
        },
      }, abort.signal);
    } catch (err) {
      if (abort.signal.aborted) return;
      const msg = err instanceof Error ? err.message : "Failed to send message";
      setError(msg);
      toast.error(msg);
      // Remove both optimistic messages on error
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id && m.id !== assistantId));
      throw err;
    } finally {
      isSendingRef.current = false;
      setIsLoading(false);
      abortRef.current = null;
    }
  };

  const confirmBacktest = async (modifiedInput: Record<string, unknown>) => {
    if (!pendingTool || !convIdRef.current) return;

    const { toolUseId, messageId, fullText: initialText, dataBlocks: initialBlocks } = pendingTool;
    setPendingTool(null);
    setIsLoading(true);
    isSendingRef.current = true;

    const abort = new AbortController();
    abortRef.current = abort;

    try {
      // Run backtest directly (no LLM)
      const bt = await runBacktest(
        {
          instrument,
          strategy: (modifiedInput.strategy ?? {}) as Record<string, unknown>,
          session: modifiedInput.session as string | undefined,
          period: modifiedInput.period as string | undefined,
          title: (modifiedInput.title as string) || "Backtest",
        },
        token,
      );

      // Continue stream — model analyzes results
      let fullText = initialText;
      const dataBlocks = [...initialBlocks];

      await sendContinueStream(
        {
          conversation_id: convIdRef.current,
          tool_use_id: toolUseId,
          tool_input: modifiedInput,
          model_response: bt.model_response,
          data_card: bt.card as unknown as Record<string, unknown>,
        },
        token,
        {
          onDataBlock(event) {
            dataBlocks.push({ ...event, status: "success" as const });
            fullText += `\n\n{{data:${dataBlocks.length - 1}}}\n\n`;
            const content = fullText;
            const data = [...dataBlocks];
            setMessages((prev) =>
              prev.map((m) => (m.id === messageId ? { ...m, content, data } : m)),
            );
          },
          onTextDelta(event) {
            fullText += event.delta;
            const content = fullText;
            setMessages((prev) =>
              prev.map((m) => (m.id === messageId ? { ...m, content } : m)),
            );
          },
          onDone(event) {
            setMessages((prev) => {
              const updated = prev.map((m) =>
                m.id === messageId
                  ? {
                      ...m,
                      content: dataBlocks.length > 0 ? fullText : event.answer,
                      usage: event.usage,
                      data: dataBlocks.length > 0 ? dataBlocks : null,
                    }
                  : m,
              );
              cacheSet(convIdRef.current!, updated);
              return updated;
            });
          },
          onPersist(event) {
            if (event.message_id) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === messageId ? { ...m, id: event.message_id } : m,
                ),
              );
            }
          },
          onError(event) {
            setError(event.error);
            toast.error(event.error);
          },
        },
        abort.signal,
      );
    } catch (err) {
      if (abort.signal.aborted) return;
      const msg = err instanceof Error ? err.message : "Failed to run backtest";
      setError(msg);
      toast.error(msg);
    } finally {
      isSendingRef.current = false;
      setIsLoading(false);
      abortRef.current = null;
    }
  };

  return { messages, isLoading, error, send, pendingTool, confirmBacktest };
}
