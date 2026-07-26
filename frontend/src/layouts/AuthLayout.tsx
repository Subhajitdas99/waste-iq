import { Outlet } from "react-router-dom";
import { ErrorBoundary } from "@/components/ErrorBoundary";

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-muted/30 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      <div
        className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-cyan-500/5 -z-10"
        aria-hidden="true"
      />
      <div
        className="absolute -top-32 -right-32 h-64 w-64 rounded-full bg-primary/10 blur-3xl -z-10"
        aria-hidden="true"
      />
      <div
        className="absolute -bottom-32 -left-32 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl -z-10"
        aria-hidden="true"
      />

      <a
        href="#auth-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:outline-none"
      >
        Skip to content
      </a>

      <div
        id="auth-content"
        className="w-full max-w-md bg-card/80 backdrop-blur-md border rounded-2xl shadow-xl p-6 md:p-8"
        tabIndex={-1}
      >
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </div>
    </div>
  );
}
