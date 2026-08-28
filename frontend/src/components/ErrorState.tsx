import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/lib/api-error";

interface ErrorStateProps {
  error: unknown;
  fallback?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
  title?: string;
  className?: string;
}

export function ErrorState({
  error,
  fallback = "Something went wrong. Please try again.",
  onRetry,
  isRetrying = false,
  title = "Unable to load",
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col gap-3 rounded-2xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <div className="flex items-start gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
        <div>
          <p className="font-medium">{title}</p>
          <p className="mt-1 text-xs opacity-90">{getApiErrorMessage(error, fallback)}</p>
        </div>
      </div>
      {onRetry ? (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onRetry}
          disabled={isRetrying}
          className="self-start border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive sm:self-auto"
          aria-busy={isRetrying}
        >
          <RefreshCw
            className={cn("mr-1.5 h-3.5 w-3.5", isRetrying && "animate-spin")}
            aria-hidden="true"
          />
          {isRetrying ? "Retrying..." : "Try again"}
        </Button>
      ) : null}
    </div>
  );
}
