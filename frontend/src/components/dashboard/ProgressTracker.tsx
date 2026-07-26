import { Check } from "lucide-react";
import { PICKUP_STATUS_FLOW, formatPickupStatus } from "@/lib/pickup";
import type { PickupStatus } from "@/types/pickup";
import { cn } from "@/lib/utils";

interface ProgressTrackerProps {
  currentStatus: PickupStatus;
  className?: string;
}

export function ProgressTracker({ currentStatus, className }: ProgressTrackerProps) {
  const currentIndex = PICKUP_STATUS_FLOW.indexOf(currentStatus);
  const isCancelled = currentStatus === "cancelled";

  return (
    <div className={cn("space-y-4", className)}>
      <div className="grid gap-3 md:grid-cols-5">
        {PICKUP_STATUS_FLOW.map((status, index) => {
          const isComplete = !isCancelled && currentIndex > index;
          const isCurrent = !isCancelled && currentIndex === index;

          return (
            <div
              key={status}
              className={cn(
                "rounded-2xl border px-4 py-3 text-sm transition-colors",
                isComplete && "border-primary/20 bg-primary/10 text-primary",
                isCurrent && "border-accent/20 bg-accent/10 text-accent-foreground dark:text-accent",
                !isComplete &&
                  !isCurrent &&
                  "border-border/80 bg-muted/40 text-muted-foreground",
              )}
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "flex h-6 w-6 items-center justify-center rounded-full border text-xs",
                    isComplete && "border-primary bg-primary text-primary-foreground",
                    isCurrent && "border-accent bg-accent text-accent-foreground",
                    !isComplete && !isCurrent && "border-border bg-background",
                  )}
                >
                  {isComplete ? <Check className="h-3.5 w-3.5" /> : index + 1}
                </span>
                <span className="font-semibold">{formatPickupStatus(status)}</span>
              </div>
            </div>
          );
        })}
      </div>

      {isCancelled ? (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-700 dark:text-rose-300">
          This pickup was cancelled before it reached the active collection stages.
        </div>
      ) : null}
    </div>
  );
}
