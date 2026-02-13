import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/components/auth/auth-provider";
import { AuthGuard } from "@/components/auth/auth-guard";
import { InstrumentsProvider } from "@/components/instruments/instruments-provider";
import { ConversationsProvider } from "@/components/conversations/conversations-provider";
import { SidebarProvider } from "@/components/sidebar/sidebar-provider";
import { ErrorBoundary } from "@/components/error-boundary";
import { RootLayout } from "@/components/layout/root-layout";
import { LoginPageContainer } from "@/pages/login/login-page.container";
import { ChatPageContainer } from "@/pages/chat/chat-page.container";
import { HomePage } from "@/pages/home/home-page";
import { InstrumentPageContainer } from "@/pages/instrument/instrument-page.container";

export function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPageContainer />} />
            <Route element={<AuthGuard />}>
              <Route element={<ErrorBoundary />}>
                <Route element={<InstrumentsProvider />}>
                  <Route element={<ConversationsProvider />}>
                    <Route element={<SidebarProvider />}>
                      <Route element={<RootLayout />}>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/i/:symbol">
                          <Route index element={<InstrumentPageContainer />} />
                          <Route path="c/:id" element={<ChatPageContainer />} />
                        </Route>
                      </Route>
                    </Route>
                  </Route>
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
