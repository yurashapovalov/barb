import { useCallback, useEffect, useRef, useState } from "react";
import { createConversation, getMessages, sendMessageStream } from "@/lib/api";
import type { DataBlock, Message } from "@/types";

interface UseChatParams {
  conversationId: string | undefined;
  token: string;
  instrument?: string;
  onConversationCreated?: (id: string) => void;
  onTitleUpdate?: (id: string, title: string) => void;
}

export type ChatState = ReturnType<typeof useChat>;

export function useChat({ conversationId, token, instrument = "NQ", onConversationCreated, onTitleUpdate }: UseChatParams) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track current conversation ID (may change after creation)
  const convIdRef = useRef(conversationId);
  convIdRef.current = conversationId;

  // Load history when opening an existing conversation.
  // Skip if we just created it (messages already in state from send()).
  const skipLoadRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const cacheRef = useRef(new Map<string, Message[]>());

  useEffect(() => {
    if (!conversationId) return;
    if (skipLoadRef.current) {
      skipLoadRef.current = false;
      return;
    }

    const cached = cacheRef.current.get(conversationId);
    if (cached) {
      setMessages(cached);
      return;
    }

    let cancelled = false;
    setMessages([]);
    setIsLoading(true);
    setError(null);

    getMessages(conversationId, token)
      .then((data) => {
        if (!cancelled) {
          setMessages(data);
          cacheRef.current.set(conversationId, data);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => { cancelled = true; };
  }, [conversationId, token]);

  const send = useCallback(async (text: string) => {
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

    let activeConvId = convIdRef.current;

    // Create conversation if needed
    if (!activeConvId) {
      try {
        const conv = await createConversation(instrument, token);
        activeConvId = conv.id;
        convIdRef.current = conv.id;
        skipLoadRef.current = true;
        onConversationCreated?.(conv.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create conversation");
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
        setIsLoading(false);
        return;
      }
    }

    const assistantId = crypto.randomUUID();
    let assistantAdded = false;

    const addAssistantMessage = () => {
      if (assistantAdded) return;
      assistantAdded = true;
      setMessages((prev) => [...prev, {
        id: assistantId,
        conversation_id: activeConvId!,
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
        onDataBlock(event) {
          addAssistantMessage();
          dataBlocks.push(event);
          const data = [...dataBlocks];
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, data } : m)),
          );
        },
        onDone(event) {
          setMessages((prev) => {
            const updated = prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: event.answer,
                    usage: event.usage,
                    data: event.data.length > 0 ? event.data : null,
                  }
                : m,
            );
            cacheRef.current.set(activeConvId!, updated);
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
          onTitleUpdate?.(activeConvId!, event.title);
        },
        onError(event) {
          setError(event.error);
        },
      }, abort.signal);
    } catch (err) {
      if (abort.signal.aborted) return;
      setError(err instanceof Error ? err.message : "Failed to send message");
      // Remove both optimistic messages on error
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id && m.id !== assistantId));
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [token, instrument, onConversationCreated, onTitleUpdate]);

  return { messages, isLoading, error, send };
}
