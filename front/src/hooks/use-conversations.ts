import { useContext } from "react";
import { ConversationsContext } from "@/components/conversations/conversations-context";

export function useConversations() {
  const ctx = useContext(ConversationsContext);
  if (!ctx) throw new Error("useConversations must be used within ConversationsProvider");
  return ctx;
}
