import { MapPin, Navigation, Package, Scale, User } from "lucide-react";

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
import { formatDateTime } from "../../utils/pickupRequests";
import { CollectorEmptyState, CollectorErrorState } from "./CollectorState";
import CollectorTimeline from "./CollectorTimeline";
import { collectorJobActions, CollectorDetailField } from "./JobCard";

export default function JobDetailsDialog({
  request,
  open,
  onOpenChange,
  trigger = null,
  triggerLabel = "View details",
  showTrigger = true,
  timeline = [],
  timelineLoading = false,
  // Action props — same contract as JobCard
  busy = false,
  actionDisabled = false,
  completeWeight = "",
  onAccept,
  onStart,
  onCollect,
  onComplete,
  onCompleteWeightChange
}) {
  const requestId = request?.id;
  const shouldLoadDetails = open && Boolean(requestId) && !request?.timeline;
  const detailQuery = usePickupRequest(requestId, {
    enabled: shouldLoadDetails,
    staleTime: 30_000
  });
  const job = detailQuery.data || request;
  const action = job ? collectorJobActions[job.status] : null;
  const isCollected = job?.status === "collected";
  const parsedWeight = Number(completeWeight);
  const canSubmitWeight = Number.isFinite(parsedWeight) && parsedWeight > 0;
  const detailTimeline = detailQuery.data?.timeline || (timeline.length > 0 ? timeline : job?.timeline || []);
  const isLoadingDetails = detailQuery.isFetching || timelineLoading;

  const hasActionHandler =
    (action?.action === "accept" && Boolean(onAccept)) ||
    (action?.action === "start" && Boolean(onStart)) ||
    (action?.action === "collect" && Boolean(onCollect)) ||
    (action?.action === "complete" && Boolean(onComplete));

  function handlePrimaryAction() {
    if (!job || !action) return;
    if (action.action === "accept") onAccept?.(job.id, job);
    else if (action.action === "start") onStart?.(job.id, job);
    else if (action.action === "collect") onCollect?.(job.id, job);
    else if (canSubmitWeight) onComplete?.(job.id, parsedWeight, job);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {showTrigger && trigger ? <DialogTrigger asChild>{trigger}</DialogTrigger> : null}
      {showTrigger && !trigger ? (
        <DialogTrigger asChild>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/80 px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink/20"
          >
            {triggerLabel}
          </button>
        </DialogTrigger>
      ) : null}

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">
            Collector Job Details
          </p>
          <DialogTitle>{job ? `Request #${job.id}` : "Pickup request"}</DialogTitle>
          <DialogDescription>
            Review the pickup location, citizen details, status, and timeline before taking the next action.
          </DialogDescription>
        </DialogHeader>

        {open && !job && isLoadingDetails ? (
          <div className="mt-4 space-y-4">
            <Skeleton className="h-28 rounded-3xl bg-white/60" />
            <div className="grid gap-3 sm:grid-cols-2">
              <Skeleton className="h-16 rounded-2xl bg-white/60" />
              <Skeleton className="h-16 rounded-2xl bg-white/60" />
              <Skeleton className="h-16 rounded-2xl bg-white/60" />
              <Skeleton className="h-16 rounded-2xl bg-white/60" />
            </div>
          </div>
        ) : null}

        {detailQuery.isError && !job ? (
          <div className="mt-6">
            <CollectorErrorState
              error={detailQuery.error}
              title="Job details unavailable"
              fallback="Close the dialog and try opening the job again."
            />
          </div>
        ) : null}

        {job ? (
          <div className="mt-4 space-y-5">
            <div className="rounded-3xl bg-white/65 p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="flex items-center gap-2 text-sm font-semibold text-leaf">
                    <Package className="h-4 w-4" />
                    {job.waste_type}
                  </p>
                  <h3 className="mt-2 font-display text-2xl text-ink">{job.address}</h3>
                </div>
                <StatusBadge status={job.status} />
              </div>
            </div>

            <section className="grid gap-3 sm:grid-cols-2" aria-label="Collector job information">
              <CollectorDetailField label="Citizen Name" value={job.citizen_name} icon={User} />
              <CollectorDetailField label="Phone" value={job.citizen_phone} />
              <CollectorDetailField label="Address" value={job.address} icon={MapPin} />
              <CollectorDetailField label="Waste Type" value={job.waste_type} icon={Package} />
              <CollectorDetailField label="Status" value={job.status} />
              <CollectorDetailField label="Created Time" value={formatDateTime(job.created_at)} />
              <CollectorDetailField
                label="Weight"
                value={job.assignment?.weight_kg ? `${job.assignment.weight_kg} kg` : null}
                icon={Scale}
              />
              <CollectorDetailField label="Assigned Collector" value={job.assigned_collector_name} />
            </section>

            {isCollected && onComplete ? (
              <label className="block">
                <span className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-ink/45">
                  <Scale className="h-3.5 w-3.5" />
                  Completion weight
                </span>
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={completeWeight}
                  onChange={(e) => onCompleteWeightChange?.(job.id, e.target.value, job)}
                  placeholder="Weight (kg)"
                  className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-leaf"
                />
              </label>
            ) : null}

            {action && hasActionHandler ? (
              <button
                type="button"
                onClick={handlePrimaryAction}
                disabled={busy || actionDisabled || (isCollected && !canSubmitWeight)}
                className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
              >
                {action.action === "start" || action.action === "collect" ? (
                  <Navigation className="h-4 w-4" />
                ) : null}
                {busy ? "Working..." : action.label}
              </button>
            ) : null}

            <CollectorTimeline
              timeline={detailTimeline}
              currentStatus={job.status}
              loading={isLoadingDetails}
            />
          </div>
        ) : (
          <div className="mt-6">
            <CollectorEmptyState
              title="No job selected"
              description="Select a collector job to inspect its details."
            />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
