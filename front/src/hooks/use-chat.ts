import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { createConversation, getMessages, sendMessageStream } from "@/lib/api";
import type { DataBlock, Message } from "@/types";

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
          // Add loading placeholder
          const loadingBlock = {
            query: {},
            result: null,
            rows: null,
            session: null,
            timeframe: null,
            source_rows: null,
            source_row_count: null,
            status: "loading" as const,
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
            // Update loading block to error state
            dataBlocks[loadingBlockIndex] = {
              ...dataBlocks[loadingBlockIndex],
              status: "error" as const,
              error: event.error,
            };
            const data = [...dataBlocks];
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, data } : m)),
            );
          }
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

  return { messages, isLoading, error, send };
}
