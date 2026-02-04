import { useState } from "react";
import { ArrowRightIcon, LoaderIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput } from "@/components/ui/input-group";

interface LoginPageProps {
  onSignIn: () => void;
  onMagicLink: (email: string) => Promise<void>;
}

export function LoginPage({ onSignIn, onMagicLink }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  async function handleMagicLink() {
    try {
      setError("");
      setSending(true);
      await onMagicLink(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send magic link");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="mx-4 w-full max-w-md text-left">
        <div className="flex size-11 items-center justify-center rounded bg-[var(--color-neutral-t1)]">
          <svg className="size-11" viewBox="0 0 44 44" fill="none">
            <path d="M13.7501 8.04005C13.7501 7.67682 14.0445 7.38235 14.4078 7.38235H19.6694C20.0326 7.38235 20.3271 7.67682 20.3271 8.04005V33.0326C20.3271 33.3958 20.0326 33.6903 19.6694 33.6903H14.4078C14.0445 33.6903 13.7501 33.3958 13.7501 33.0326V8.04005Z" fill="currentColor" />
            <path d="M23.6729 17.9055C23.6729 17.5423 23.9674 17.2478 24.3306 17.2478H29.5922C29.9555 17.2478 30.2499 17.5423 30.2499 17.9055V33.0326C30.2499 33.3958 29.9555 33.6903 29.5922 33.6903H24.3306C23.9674 33.6903 23.6729 33.3958 23.6729 33.0326V17.9055Z" fill="currentColor" />
          </svg>
        </div>
        <div className="my-6 flex flex-col gap-1">
          <span className="text-3xl font-medium tracking-tight">Barb</span>
          <p className="text-base text-muted-foreground">Sign up or log in to continue</p>
        </div>
        <Button variant="outline" size="lg" className="w-full" onClick={onSignIn}>
          <svg className="size-5" viewBox="0 0 24 24">
            <path
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
              fill="#4285F4"
            />
            <path
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              fill="#FBBC05"
            />
            <path
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              fill="#EA4335"
            />
          </svg>
          Continue with Google
        </Button>
        <div className="my-6 text-center text-sm text-muted-foreground">or</div>
        <InputGroup className="h-[44px] rounded-md bg-transparent [box-shadow:none]">
          <InputGroupInput className="h-full text-base md:text-base" type="email" placeholder="Enter your email..." value={email} onChange={(e) => setEmail(e.target.value)} />
          <InputGroupAddon align="inline-end">
            <InputGroupButton size="icon-sm" variant="ghost" disabled={!isValidEmail || sending} onClick={handleMagicLink}>
              {sending ? <LoaderIcon className="size-5 animate-spin" /> : <ArrowRightIcon className="size-5" />}
            </InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
        {sent && <p className="mt-3 text-sm text-muted-foreground">Check your email for a login link.</p>}
        {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
      </div>
    </div>
  );
}
