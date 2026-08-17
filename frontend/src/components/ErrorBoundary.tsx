import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Unhandled render error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <main
          role="alert"
          className="flex min-h-screen flex-col items-center justify-center p-6 text-center"
        >
          <AlertTriangle className="mb-4 h-14 w-14 text-destructive" aria-hidden="true" />
          <h1 className="mb-2 text-2xl font-bold">Something went wrong</h1>
          <p className="mb-6 max-w-md text-muted-foreground">
            Waste-IQ could not render this page. Reload the application to start with a fresh session.
          </p>
          <Button onClick={() => window.location.reload()} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Reload application
          </Button>
        </main>
      );
    }

    return this.props.children;
  }
}
