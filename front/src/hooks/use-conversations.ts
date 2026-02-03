import { useContext } from "react";
import { ConversationsContext } from "@/components/conversations/conversations-provider";

export function useConversations() {
  const ctx = useContext(ConversationsContext);
  if (!ctx) throw new Error("useConversations must be used within ConversationsProvider");
  return ctx;
}
