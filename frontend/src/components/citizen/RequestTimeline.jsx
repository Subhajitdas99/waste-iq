import StatusBadge from "../StatusBadge";
import { citizenTimelineFlow, formatDateTime, formatRequestStatus } from "../../utils/pickupRequests";

function TimelineStep({ status, currentStatus, event }) {
  const isCurrent = currentStatus === status;
  const isCompleted = Boolean(event) && !isCurrent;

  return (
    <div className="relative rounded-3xl border border-white/60 bg-white/65 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="font-semibold text-ink">{formatRequestStatus(status)}</p>
        <div
          className={`h-3 w-3 rounded-full ${
            isCurrent ? "bg-ink ring-4 ring-ink/10" : isCompleted ? "bg-leaf" : "bg-ink/15"
          }`}
        />
      </div>
      <p className="mt-2 text-sm text-ink/65">
        {event ? formatDateTime(event.created_at) : "Waiting for this milestone"}
      </p>
      {event?.note ? <p className="mt-3 text-sm text-ink/75">{event.note}</p> : null}
    </div>
  );
}

export default function RequestTimeline({ timeline, currentStatus }) {
  const timelineMap = new Map(timeline.map((event) => [event.status, event]));
  const flow = currentStatus === "cancelled" ? ["pending", "cancelled"] : citizenTimelineFlow;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        {timeline.map((event) => (
          <div key={event.id} className="rounded-2xl bg-white/65 px-3 py-2">
            <StatusBadge status={event.status} />
          </div>
        ))}
      </div>

      <div className="grid gap-4">
        {flow.map((status) => (
          <TimelineStep key={status} status={status} currentStatus={currentStatus} event={timelineMap.get(status)} />
        ))}
      </div>

      <div className="rounded-3xl border border-dashed border-ink/10 bg-white/55 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Event Feed</p>
        <div className="mt-4 space-y-4">
          {timeline.map((event) => (
            <div key={event.id} className="rounded-2xl bg-white/75 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <StatusBadge status={event.status} />
                <p className="text-sm text-ink/60">{formatDateTime(event.created_at)}</p>
              </div>
              <p className="mt-3 text-sm text-ink/75">{event.note || "Status updated."}</p>
              <p className="mt-2 text-xs uppercase tracking-[0.24em] text-ink/45">
                {event.actor_name ? `${event.actor_name} - ${formatRequestStatus(event.actor_role)}` : "System event"}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
