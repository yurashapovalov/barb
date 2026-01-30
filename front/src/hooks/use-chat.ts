import { useCallback, useEffect, useRef, useState } from "react";
import { createConversation, getMessages, sendMessage } from "@/lib/api";
import type { Message } from "@/types";

interface UseChatParams {
  conversationId: string | undefined;
  token: string;
  instrument?: string;
  onConversationCreated?: (id: string) => void;
}

export function useChat({ conversationId, token, instrument = "NQ", onConversationCreated }: UseChatParams) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track current conversation ID (may change after creation)
  const convIdRef = useRef(conversationId);
  convIdRef.current = conversationId;

  // Load history when opening an existing conversation.
  // Skip if we just created it (messages already in state from send()).
  const skipLoadRef = useRef(false);

  useEffect(() => {
    if (!conversationId) return;
    if (skipLoadRef.current) {
      skipLoadRef.current = false;
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getMessages(conversationId, token)
      .then((data) => {
        if (!cancelled) setMessages(data);
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
        return;
      }
    }

    // Optimistic user message
    const userMsg: Message = {
      id: crypto.randomUUID(),
      conversation_id: activeConvId,
      role: "user",
      content: text,
      data: null,
      usage: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendMessage(activeConvId, text, token);

      const assistantMsg: Message = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        role: "model",
        content: response.answer,
        data: response.data.length > 0 ? response.data : null,
        usage: response.usage,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setIsLoading(false);
    }
  }, [token, onConversationCreated]);

  return { messages, isLoading, error, send };
}
