import { Component, type ErrorInfo, type ReactNode } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface Props {
  children?: ReactNode;
  resetKey?: string;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidUpdate(prevProps: Props) {
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Uncaught error:", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children ?? <Outlet />;

    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-full max-w-sm space-y-4 text-center">
          <h1 className="text-lg font-semibold">Something went wrong</h1>
          <p className="text-sm text-muted-foreground">{this.state.error.message}</p>
          <Button onClick={() => window.location.reload()}>Reload</Button>
        </div>
      </div>
    );
  }
}

// Wrapper that resets error boundary on route navigation
export function RouteErrorBoundary() {
  const { pathname } = useLocation();
  return <ErrorBoundary resetKey={pathname}><Outlet /></ErrorBoundary>;
}
