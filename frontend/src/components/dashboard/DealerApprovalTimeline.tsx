import type { DealerApprovalEvent } from "@/types/dealer";
import {
  dealerApprovalStatusConfig,
  formatDealerApprovalStatus,
} from "@/lib/dealerApproval";
import { formatDateTime } from "@/lib/pickup";
import { cn } from "@/lib/utils";

interface DealerApprovalTimelineProps {
  events: DealerApprovalEvent[];
}

export function DealerApprovalTimeline({ events }: DealerApprovalTimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No approval activity has been recorded yet.
      </p>
    );
  }

  return (
    <ol className="space-y-4">
      {events.map((event) => {
        const config =
          dealerApprovalStatusConfig[event.status] ??
          dealerApprovalStatusConfig.draft;

        return (
          <li key={event.id} className="flex gap-3">
            <span className="flex flex-col items-center">
              <span
                className={cn("mt-1.5 h-3 w-3 shrink-0 rounded-full", config.dotClassName)}
                aria-hidden="true"
              />
              <span className="w-px flex-1 bg-border" aria-hidden="true" />
            </span>
            <div className="pb-1">
              <p className="text-sm font-semibold capitalize">
                {formatDealerApprovalStatus(event.status)}
              </p>
              <p className="text-sm text-muted-foreground">
                {event.note ?? "No additional note was provided."}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground/70">
                {event.actor_name ?? "System"} - {formatDateTime(event.created_at)}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
