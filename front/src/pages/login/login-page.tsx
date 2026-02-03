import { Button } from "@/components/ui/button";

interface LoginPageProps {
  onSignIn: () => void;
}

export function LoginPage({ onSignIn }: LoginPageProps) {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm space-y-6 text-center">
        <h1 className="text-2xl font-bold">Barb</h1>
        <Button className="w-full" onClick={onSignIn}>
          Sign in with Google
        </Button>
      </div>
    </div>
  );
}
