import { CollectorEmptyState, CollectorErrorState } from "./CollectorState";
import JobCard, { JobListSkeleton } from "./JobCard";
import { Navigation } from "lucide-react";

export default function AssignedPickupList({
  jobs = [],
  loading = false,
  error = "",
  busyId = null,
  actionDisabled = false,
  completeWeights = {},
  onStart,
  onCollect,
  onComplete,
  onCompleteWeightChange,
  onViewDetails,
  onNavigate,
  onSelectPickup,
  selectedPickupId = null,
  navigationLoading = false,
  emptyTitle = "No assignments yet",
  emptyDescription = "Accept a request from the available list to get started."
}) {
  if (loading) {
    return <JobListSkeleton label="Loading assigned pickup jobs" />;
  }

  if (error) {
    return (
      <CollectorErrorState
        error={error}
        title="Assigned jobs unavailable"
        fallback="Unable to load assigned jobs."
      />
    );
  }

  if (jobs.length === 0) {
    return (
      <CollectorEmptyState title={emptyTitle} description={emptyDescription} />
    );
  }

  return (
    <section className="grid gap-4 lg:grid-cols-2" aria-label="Assigned pickup jobs">
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          request={job}
          busy={busyId === job.id}
          actionDisabled={actionDisabled}
          completeWeight={completeWeights[job.id] ?? ""}
          onStart={onStart}
          onCollect={onCollect}
          onComplete={onComplete}
          onCompleteWeightChange={onCompleteWeightChange}
          onViewDetails={(request) => {
            onSelectPickup?.(request);
            onViewDetails?.(request);
          }}
          cardClassName={selectedPickupId === job.id ? "ring-2 ring-ink/30" : ""}
          footerSlot={
            <button
              type="button"
              onClick={() => onNavigate?.(job)}
              disabled={navigationLoading}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-leaf px-4 py-2.5 text-sm font-semibold text-sand transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Navigation className="h-4 w-4" />
              Navigate
            </button>
          }
        />
      ))}
    </section>
  );
}
