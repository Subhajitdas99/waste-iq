import { CheckCircle2, Navigation, Package, Scale } from "lucide-react";

import { Card, CardContent } from "../../components/ui/card";
import { Skeleton } from "../../components/ui/skeleton";
import { CollectorErrorState } from "./CollectorState";

const defaultCards = [
  {
    label: "Total Pickups",
    field: "total_assigned",
    icon: Package,
    color: "text-ink",
    format: (value) => value ?? 0
  },
  {
    label: "Active Jobs",
    field: "active_jobs",
    icon: Navigation,
    color: "text-blue-600",
    format: (value) => value ?? 0
  },
  {
    label: "Completed Jobs",
    field: "completed_jobs",
    icon: CheckCircle2,
    color: "text-leaf",
    format: (value) => value ?? 0
  },
  {
    label: "Weight Collected",
    field: "total_weight_kg",
    icon: Scale,
    color: "text-amber-600",
    format: (value) => `${value ?? 0} kg`
  }
];

function SummarySkeleton() {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Loading collector summary">
      {defaultCards.map((card) => (
        <Card key={card.field} className="p-5">
          <Skeleton className="h-3 w-32 rounded-full bg-leaf/15" />
          <Skeleton className="mt-5 h-9 w-24 rounded-2xl" />
          <Skeleton className="mt-4 h-3 w-full rounded-full" />
        </Card>
      ))}
    </section>
  );
}

export default function SummaryCards({ summary, loading = false, error = null, cards = defaultCards }) {
  if (loading) {
    return <SummarySkeleton />;
  }

  if (error) {
    return (
      <CollectorErrorState
        error={error}
        title="Collector summary unavailable"
        fallback="Unable to load collector summary."
      />
    );
  }

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Collector summary">
      {cards.map((card) => {
        const Icon = card.icon;
        const value = card.format ? card.format(summary?.[card.field]) : summary?.[card.field];

        return (
          <Card key={card.field} className="overflow-hidden">
            <CardContent className="flex items-center justify-between gap-4 p-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-ink/40">{card.label}</p>
                <p className={`mt-3 font-display text-3xl ${card.color}`}>{value}</p>
              </div>
              {Icon ? <Icon className={`h-8 w-8 shrink-0 opacity-30 ${card.color}`} /> : null}
            </CardContent>
          </Card>
        );
      })}
    </section>
  );
}
