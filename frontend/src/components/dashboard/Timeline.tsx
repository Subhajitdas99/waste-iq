import { formatDateTime, formatPickupStatus, pickupStatusConfig } from "@/lib/pickup";
import type { PickupTimelineEvent } from "@/types/pickup";
import { cn } from "@/lib/utils";

interface TimelineProps {
  events: PickupTimelineEvent[];
  className?: string;
}

export function Timeline({ events, className }: TimelineProps) {
  const sortedEvents = [...events].sort(
    (left, right) =>
      new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
  );

  return (
    <ol className={cn("space-y-4", className)}>
      {sortedEvents.map((event, index) => {
        const statusConfig =
          pickupStatusConfig[event.status] ?? pickupStatusConfig.pending;

        return (
          <li key={event.id} className="relative pl-8">
            {index !== sortedEvents.length - 1 ? (
              <span
                className="absolute left-[11px] top-6 h-[calc(100%-0.5rem)] w-px bg-border"
                aria-hidden="true"
              />
            ) : null}
            <span
              className={cn(
                "absolute left-0 top-1 h-6 w-6 rounded-full border-4 border-background",
                statusConfig.dotClassName,
              )}
              aria-hidden="true"
            />
            <div className="rounded-2xl border bg-muted/20 p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold">{formatPickupStatus(event.status)}</p>
                  {event.note ? (
                    <p className="mt-1 text-sm text-muted-foreground">{event.note}</p>
                  ) : null}
                </div>
                <p className="text-sm text-muted-foreground">
                  {formatDateTime(event.created_at)}
                </p>
              </div>
              {(event.actor_name || event.actor_role) && (
                <p className="mt-3 text-sm text-muted-foreground">
                  {event.actor_name ?? "System"}
                  {event.actor_role ? ` (${event.actor_role})` : ""}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
