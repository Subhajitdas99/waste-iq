import { CollectorEmptyState, CollectorErrorState } from "./CollectorState";
import JobCard, { JobListSkeleton } from "./JobCard";

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
          onViewDetails={onViewDetails}
        />
      ))}
    </section>
  );
}
