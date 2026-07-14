import { Clock3, UserRound } from "lucide-react";

import StatusBadge from "../../components/StatusBadge";
import { Card } from "../../components/ui/card";
import { Skeleton } from "../../components/ui/skeleton";
import { citizenTimelineFlow, formatDateTime, formatRequestStatus } from "../../utils/pickupRequests";
import { CollectorEmptyState } from "./CollectorState";

const milestoneLabels = {
  pending: "Requested",
  accepted: "Accepted",
  on_the_way: "On The Way",
  collected: "Collected",
  completed: "Completed"
};

function TimelineSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {citizenTimelineFlow.map((status) => (
        <Card key={status} className="p-4">
          <Skeleton className="h-3 w-28 rounded-full bg-leaf/15" />
          <Skeleton className="mt-5 h-5 w-44 rounded-full" />
          <Skeleton className="mt-3 h-4 w-full rounded-full" />
        </Card>
      ))}
    </div>
  );
}

function TimelineMilestone({ status, event }) {
  const reached = Boolean(event);

  return (
    <article
      className={`rounded-3xl border p-4 ${
        reached ? "border-leaf/20 bg-white/75" : "border-dashed border-ink/10 bg-white/45"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">
            {milestoneLabels[status] || formatRequestStatus(status)}
          </p>
          <h3 className="mt-2 font-display text-xl text-ink">{reached ? "Completed milestone" : "Awaiting update"}</h3>
        </div>
        <StatusBadge status={status} />
      </div>

      <dl className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-sand/70 px-4 py-3">
          <dt className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-ink/45">
            <UserRound className="h-3.5 w-3.5" />
            Actor
          </dt>
          <dd className="mt-2 text-sm font-semibold text-ink">{event?.actor_name || "System"}</dd>
        </div>
        <div className="rounded-2xl bg-sand/70 px-4 py-3">
          <dt className="text-xs font-semibold uppercase tracking-[0.22em] text-ink/45">Role</dt>
          <dd className="mt-2 text-sm font-semibold text-ink">
            {event?.actor_role ? formatRequestStatus(event.actor_role) : "System"}
          </dd>
        </div>
        <div className="rounded-2xl bg-sand/70 px-4 py-3 sm:col-span-2">
          <dt className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-ink/45">
            <Clock3 className="h-3.5 w-3.5" />
            Timestamp
          </dt>
          <dd className="mt-2 text-sm font-semibold text-ink">
            {event?.created_at ? formatDateTime(event.created_at) : "Not reached yet"}
          </dd>
        </div>
      </dl>

      <div className="mt-4 rounded-2xl bg-white/70 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-ink/45">Notes</p>
        <p className="mt-2 text-sm leading-6 text-ink/75">{event?.note || "No timeline note yet."}</p>
      </div>
    </article>
  );
}

export default function CollectorTimeline({
  timeline = [],
  currentStatus = "",
  loading = false,
  emptyMessage = "No timeline updates have been recorded yet."
}) {
  if (loading) {
    return <TimelineSkeleton />;
  }

  const eventsByStatus = new Map(timeline.map((event) => [event.status, event]));

  return (
    <div className="space-y-5">
      {currentStatus ? (
        <div className="rounded-3xl bg-white/65 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">Current Status</p>
          <div className="mt-3">
            <StatusBadge status={currentStatus} />
          </div>
        </div>
      ) : null}

      {timeline.length === 0 ? (
        <CollectorEmptyState title="No timeline yet" description={emptyMessage} />
      ) : null}

      <section className="grid gap-4 md:grid-cols-2" aria-label="Collector pickup timeline">
        {citizenTimelineFlow.map((status) => (
          <TimelineMilestone key={status} status={status} event={eventsByStatus.get(status)} />
        ))}
      </section>
    </div>
  );
}
