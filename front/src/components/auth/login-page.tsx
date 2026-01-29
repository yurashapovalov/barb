import { Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";

export function LoginPage() {
  const { session, loading, signInWithGoogle } = useAuth();

  if (loading) return null;
  if (session) return <Navigate to="/" replace />;

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm space-y-6 text-center">
        <h1 className="text-2xl font-bold">Barb</h1>
        <button
          onClick={signInWithGoogle}
          className="w-full rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
