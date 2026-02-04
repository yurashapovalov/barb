import { useNavigate, useParams } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import { useChat } from "@/hooks/use-chat";
import { useConversations } from "@/hooks/use-conversations";
import { ChatPage } from "./chat-page";

export function ChatPageContainer() {
  const { id } = useParams<{ id: string }>();
  const { session } = useAuth();
  const { conversations, loading, updateTitle } = useConversations();
  const navigate = useNavigate();
  const token = session?.access_token ?? "";

  // Redirect to most recent conversation on bare "/"
  useEffect(() => {
    if (!loading && !id && conversations.length > 0) {
      navigate(`/c/${conversations[0].id}`, { replace: true });
    }
  }, [loading, id, conversations, navigate]);

  const onConversationCreated = (convId: string) =>
    navigate(`/c/${convId}`, { replace: true });

  const { messages, isLoading, error, send } = useChat({
    conversationId: id,
    token,
    onConversationCreated,
    onTitleUpdate: updateTitle,
  });

  if (loading) return null;

  const conversation = conversations.find((c) => c.id === id);

  return <ChatPage conversationId={id} title={conversation?.title} messages={messages} isLoading={isLoading} error={error} send={send} />;
}
