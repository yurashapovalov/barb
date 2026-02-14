import { createContext } from "react";
import type { Conversation } from "@/types";

export interface ConversationsContextValue {
  conversations: Conversation[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
  retry: () => void;
  updateTitle: (id: string, title: string) => void;
  create: (instrument: string) => Promise<Conversation>;
  remove: (id: string) => Promise<void>;
}

export const ConversationsContext = createContext<ConversationsContextValue | null>(null);
