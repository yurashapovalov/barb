import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/components/auth/auth-provider";
import { AuthGuard } from "@/components/auth/auth-guard";
import { ConversationsProvider } from "@/components/conversations/conversations-provider";
import { ErrorBoundary } from "@/components/error-boundary";
import { RootLayout } from "@/components/layout/root-layout";
import { LoginPageContainer } from "@/pages/login/login-page.container";
import { ChatPageContainer } from "@/pages/chat/chat-page.container";

export function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPageContainer />} />
            <Route element={<AuthGuard />}>
              <Route element={<ConversationsProvider />}>
                <Route element={<RootLayout />}>
                  <Route path="/" element={<ChatPageContainer />} />
                  <Route path="/c/:id" element={<ChatPageContainer />} />
                </Route>
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
