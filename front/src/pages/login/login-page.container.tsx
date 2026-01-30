import { Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { LoginPage } from "./login-page";

export function LoginPageContainer() {
  const { session, loading, signInWithGoogle } = useAuth();

  if (loading) return null;
  if (session) return <Navigate to="/" replace />;

  return <LoginPage onSignIn={signInWithGoogle} />;
}
