import { useContext } from "react";
import { ConversationsContext, type ConversationsContextValue } from "@/components/conversations/conversations-context";

export function useConversations(): ConversationsContextValue {
  const ctx = useContext(ConversationsContext);
  if (!ctx) throw new Error("useConversations must be used within ConversationsProvider");
  return ctx;
}

export function useOptionalConversations(): ConversationsContextValue | null {
  return useContext(ConversationsContext);
}
