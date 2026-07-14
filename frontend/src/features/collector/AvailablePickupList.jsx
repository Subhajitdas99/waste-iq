import { CollectorEmptyState, CollectorErrorState } from "./CollectorState";
import JobCard, { JobListSkeleton } from "./JobCard";

export default function AvailablePickupList({
  pickups = [],
  loading = false,
  error = "",
  busyId = null,
  actionDisabled = false,
  onAccept,
  onViewDetails,
  emptyTitle = "No open leads right now",
  emptyDescription = "Check back soon for new pickup requests in your area."
}) {
  if (loading) {
    return <JobListSkeleton label="Loading available pickup requests" />;
  }

  if (error) {
    return (
      <CollectorErrorState
        error={error}
        title="Available pickups unavailable"
        fallback="Unable to load available pickups."
      />
    );
  }

  if (pickups.length === 0) {
    return (
      <CollectorEmptyState title={emptyTitle} description={emptyDescription} />
    );
  }

  return (
    <section className="grid gap-4 lg:grid-cols-2" aria-label="Available pickup requests">
      {pickups.map((pickup) => (
        <JobCard
          key={pickup.id}
          request={pickup}
          busy={busyId === pickup.id}
          actionDisabled={actionDisabled}
          onAccept={onAccept}
          onViewDetails={onViewDetails}
        />
      ))}
    </section>
  );
}
