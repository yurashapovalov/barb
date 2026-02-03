import { useNavigate, useParams } from "react-router-dom";
import { useCallback } from "react";
import { useAuth } from "@/hooks/use-auth";
import { useChat } from "@/hooks/use-chat";
import { useConversations } from "@/hooks/use-conversations";
import { ChatPage } from "./chat-page";

export function ChatPageContainer() {
  const { id } = useParams<{ id: string }>();
  const { session } = useAuth();
  const { refresh } = useConversations();
  const navigate = useNavigate();

  const token = session?.access_token ?? "";

  const onConversationCreated = useCallback(
    (convId: string) => navigate(`/c/${convId}`, { replace: true }),
    [navigate],
  );

  const { messages, error, send } = useChat({
    conversationId: id,
    token,
    onConversationCreated,
    onTitleUpdate: refresh,
  });

  return <ChatPage messages={messages} error={error} send={send} />;
}
