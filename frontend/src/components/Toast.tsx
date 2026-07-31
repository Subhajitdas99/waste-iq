import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ToastProps {
  message: string;
  type?: "default" | "success" | "error";
  onDismiss?: () => void;
}

export function Toast({ message, type = "default", onDismiss }: ToastProps) {
  return (
    <div
      role={type === "error" ? "alert" : "status"}
      aria-live={type === "error" ? "assertive" : "polite"}
      aria-atomic="true"
      className={cn(
        "fixed bottom-4 right-4 z-50 flex max-w-md items-start gap-3 rounded-md border p-4 text-sm font-medium shadow-md",
        type === "default" && "bg-background text-foreground",
        type === "success" && "border-primary bg-primary text-primary-foreground",
        type === "error" && "border-destructive bg-destructive text-destructive-foreground",
      )}
    >
      <span className="flex-1">{message}</span>
      {onDismiss ? (
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-sm p-0.5 opacity-90 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-current focus:ring-offset-2"
          aria-label="Dismiss notification"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}
