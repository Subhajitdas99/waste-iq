import { Leaf, Recycle, Sprout } from "lucide-react";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import {
  formatImpactNumber,
  type RecyclingImpactMetrics,
} from "@/lib/recycling";

interface RecyclingImpactCardProps {
  metrics: RecyclingImpactMetrics | null;
  isLoading?: boolean;
}

export function RecyclingImpactCard({ metrics, isLoading = false }: RecyclingImpactCardProps) {
  return (
    <DashboardCard
      title="Recycling Impact"
      description="Environmental impact of your completed collections, calculated from verified pickup weights."
    >
      {isLoading && !metrics ? (
        <LoadingSkeleton count={1} />
      ) : metrics && metrics.totalPickups > 0 ? (
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border bg-muted/20 p-5">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Recycle className="h-4 w-4 text-primary" />
              Total Recycled
            </div>
            <p className="mt-3 text-3xl font-bold tracking-tight">
              {formatImpactNumber(metrics.totalWeightKg)}
              <span className="ml-1 text-base font-medium text-muted-foreground">kg</span>
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Across {metrics.totalPickups} completed pickup{metrics.totalPickups === 1 ? "" : "s"}
            </p>
          </div>

          <div className="rounded-2xl border bg-muted/20 p-5">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Leaf className="h-4 w-4 text-emerald-500" />
              CO₂ Saved
            </div>
            <p className="mt-3 text-3xl font-bold tracking-tight">
              {formatImpactNumber(metrics.co2SavedKg)}
              <span className="ml-1 text-base font-medium text-muted-foreground">kg</span>
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Using ~0.42 kg CO₂e saved per kg recycled
            </p>
          </div>

          <div className="rounded-2xl border bg-muted/20 p-5">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Sprout className="h-4 w-4 text-emerald-500" />
              Eco Points
            </div>
            <p className="mt-3 text-3xl font-bold tracking-tight">
              {formatImpactNumber(metrics.ecoPoints)}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Rewarded at {10} points per kg recycled
            </p>
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed bg-muted/20 px-4 py-8 text-center text-sm text-muted-foreground">
          Impact metrics appear after your first completed pickup with a reported weight.
        </div>
      )}
    </DashboardCard>
  );
}
