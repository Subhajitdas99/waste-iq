import { Clock3, UserRound } from "lucide-react";

import StatusBadge from "../../components/StatusBadge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "../../components/ui/dialog";
import { Skeleton } from "../../components/ui/skeleton";
import { usePickupRequest } from "../../hooks/usePickupRequests";
import { citizenTimelineFlow, formatDateTime, formatRequestStatus } from "../../utils/pickupRequests";

const milestoneLabels = {
  pending: "Requested",
  accepted: "Accepted",
  on_the_way: "On The Way",
  collected: "Collected",
  completed: "Completed"
};

function getMilestoneLabel(status) {
  return milestoneLabels[status] || formatRequestStatus(status);
}

function TimelineSkeleton() {
  return (
    <div className="mt-6 grid gap-4 lg:grid-cols-2">
      {citizenTimelineFlow.map((status) => (
        <div key={status} className="rounded-3xl border border-white/60 bg-white/60 p-4">
          <Skeleton className="h-3 w-28 rounded-full bg-leaf/15" />
          <Skeleton className="mt-5 h-4 w-40 rounded-full" />
          <Skeleton className="mt-3 h-4 w-full rounded-full" />
          <Skeleton className="mt-2 h-4 w-3/4 rounded-full" />
        </div>
      ))}
    </div>
  );
}

function TimelineMilestone({ event, status }) {
  const hasEvent = Boolean(event);

  return (
    <article
      className={`rounded-3xl border p-4 transition ${
        hasEvent ? "border-leaf/20 bg-white/75" : "border-dashed border-ink/10 bg-white/45"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">
            {getMilestoneLabel(status)}
          </p>
          <h3 className="mt-2 font-display text-2xl text-ink">{hasEvent ? "Completed milestone" : "Awaiting update"}</h3>
        </div>
        <StatusBadge status={status} />
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-sand/70 px-4 py-3">
          <dt className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-ink/45">
            <UserRound className="h-3.5 w-3.5" />
            Actor
          </dt>
          <dd className="mt-2 text-sm font-semibold text-ink">{event?.actor_name || "System"}</dd>
        </div>
        <div className="rounded-2xl bg-sand/70 px-4 py-3">
          <dt className="text-xs font-semibold uppercase tracking-[0.24em] text-ink/45">Role</dt>
          <dd className="mt-2 text-sm font-semibold text-ink">
            {event?.actor_role ? formatRequestStatus(event.actor_role) : "System"}
          </dd>
        </div>
        <div className="rounded-2xl bg-sand/70 px-4 py-3 sm:col-span-2">
          <dt className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-ink/45">
            <Clock3 className="h-3.5 w-3.5" />
            Timestamp
          </dt>
          <dd className="mt-2 text-sm font-semibold text-ink">
            {event?.created_at ? formatDateTime(event.created_at) : "Not reached yet"}
          </dd>
        </div>
      </dl>

      <div className="mt-4 rounded-2xl bg-white/70 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink/45">Notes</p>
        <p className="mt-2 text-sm leading-6 text-ink/75">{event?.note || "No timeline note yet."}</p>
      </div>
    </article>
  );
}

function TimelineContent({ request }) {
  const timeline = request.timeline || [];
  const eventsByStatus = new Map(timeline.map((event) => [event.status, event]));

  return (
    <div className="mt-6 space-y-5">
      <div className="rounded-3xl bg-white/65 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">Current Status</p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <StatusBadge status={request.status} />
          <p className="text-sm text-ink/70">{request.waste_type}</p>
        </div>
      </div>

      {timeline.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-ink/10 bg-white/65 p-5">
          <p className="font-display text-2xl text-ink">No timeline yet</p>
          <p className="mt-2 text-sm leading-6 text-ink/70">
            This pickup request has no timeline events yet. Updates will appear here as soon as the request changes status.
          </p>
        </div>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-2" aria-label="Pickup request timeline">
        {citizenTimelineFlow.map((status) => (
          <TimelineMilestone key={status} status={status} event={eventsByStatus.get(status)} />
        ))}
      </section>
    </div>
  );
}

export default function PickupTimeline({ requestId, triggerLabel = "View Timeline" }) {
  const { data: request, error, isError, isPending } = usePickupRequest(requestId);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          disabled={!requestId}
          className="inline-flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/80 px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Clock3 className="h-4 w-4" />
          {triggerLabel}
        </button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Pickup Timeline</p>
          <DialogTitle>{request ? `Request #${request.id}` : "Pickup request journey"}</DialogTitle>
          <DialogDescription>
            Review each status transition with the actor, role, timestamp, and notes returned by the pickup request API.
          </DialogDescription>
        </DialogHeader>

        {isPending ? <TimelineSkeleton /> : null}

        {isError ? (
          <div className="mt-6 rounded-3xl border border-coral/30 bg-coral/10 p-5" role="alert">
            <p className="font-semibold text-coral">
              {!error?.response ? "No internet connection" : "Unable to load this pickup timeline."}
            </p>
            <p className="mt-2 text-sm text-ink/70">
              {!error?.response
                ? "Reconnect and open the timeline again."
                : error.response?.data?.detail || "Please try opening the timeline again."}
            </p>
          </div>
        ) : null}

        {!isPending && !isError && request ? <TimelineContent request={request} /> : null}
      </DialogContent>
    </Dialog>
  );
}
