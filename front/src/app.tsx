import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/components/auth/auth-provider";
import { AuthGuard } from "@/components/auth/auth-guard";
import { RootLayout } from "@/components/layout/root-layout";
import { LoginPageContainer } from "@/pages/login/login-page.container";
import { ChatPageContainer } from "@/pages/chat/chat-page.container";

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPageContainer />} />
          <Route element={<AuthGuard />}>
            <Route element={<RootLayout />}>
              <Route path="/" element={<ChatPageContainer />} />
              <Route path="/c/:id" element={<ChatPageContainer />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
