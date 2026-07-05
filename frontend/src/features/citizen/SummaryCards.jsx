import { getApiError } from "../../api/client";
import { Skeleton } from "../../components/ui/skeleton";
import { useCitizenSummary } from "../../hooks/usePickupRequests";

const summaryCards = [
  {
    label: "Total Requests",
    field: "total_requests",
    hint: "All pickup requests you have created"
  },
  {
    label: "Pending",
    field: "pending_requests",
    hint: "Requests waiting for collector acceptance"
  },
  {
    label: "Accepted",
    field: "accepted_requests",
    hint: "Requests accepted by a collector"
  },
  {
    label: "Completed",
    field: "completed_requests",
    hint: "Pickups confirmed as fully completed"
  }
];

function SummarySkeleton() {
  return (
    <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4" aria-label="Loading citizen summary">
      {summaryCards.map((card) => (
        <div key={card.field} className="glass-panel rounded-3xl border border-white/60 p-5 shadow-glow">
          <Skeleton className="h-3 w-32 rounded-full bg-leaf/15" />
          <Skeleton className="mt-5 h-10 w-20 rounded-2xl" />
          <Skeleton className="mt-4 h-3 w-full rounded-full" />
          <Skeleton className="mt-2 h-3 w-3/4 rounded-full" />
        </div>
      ))}
    </section>
  );
}

export default function SummaryCards() {
  const { data: summary, error, isError, isPending } = useCitizenSummary();

  if (isPending) {
    return <SummarySkeleton />;
  }

  if (isError) {
    return (
      <section className="glass-panel rounded-3xl border border-coral/30 bg-coral/10 p-5 shadow-glow" role="alert">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-coral">Summary unavailable</p>
        <p className="mt-3 text-sm text-ink/70">
          {!error?.response
            ? "No internet connection. Reconnect and refresh to load your pickup request summary."
            : getApiError(error, "Unable to load your pickup request summary.")}
        </p>
      </section>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4" aria-label="Citizen pickup summary">
      {summaryCards.map((card) => (
        <div key={card.field} className="glass-panel rounded-3xl border border-white/60 p-5 shadow-glow">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">{card.label}</p>
          <p className="mt-3 font-display text-4xl text-ink">{summary[card.field]}</p>
          <p className="mt-2 text-sm text-ink/70">{card.hint}</p>
        </div>
      ))}
    </section>
  );
}
