import { Scale, Truck, User } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { formatDateTime, formatWeight } from "@/lib/pickup";
import type { AdminDisputedPickup } from "@/types/pickup";
import { cn } from "@/lib/utils";

interface WeightDisputeCardProps {
  request: AdminDisputedPickup;
  onUphold: (requestId: number) => void;
  onCorrect: (requestId: number) => void;
  isPending?: boolean;
}

function formatDisputeResolution(
  resolution: string | null,
): string | null {
  if (!resolution) return null;
  return resolution === "upheld" ? "Upheld" : "Corrected";
}

export function WeightDisputeCard({
  request,
  onUphold,
  onCorrect,
  isPending = false,
}: WeightDisputeCardProps) {
  const estimated = request.estimated_weight_kg;
  const collectorWeight = request.assignment?.weight_kg;
  const diff =
    estimated !== null && estimated !== undefined &&
    collectorWeight !== null && collectorWeight !== undefined
      ? Math.abs(estimated - collectorWeight)
      : null;

  return (
    <Card className={cn("border-white/40 bg-card/85 shadow-sm", isPending && "opacity-60")}>
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3" role="group" aria-label="Request status">
              <span className="text-sm font-medium text-muted-foreground">
                Request #{request.id}
              </span>
              <StatusBadge status={request.status} />
              {request.dispute.resolution && (
                <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                  {formatDisputeResolution(request.dispute.resolution)}
                </span>
              )}
            </div>
            <h3 className="mt-3 text-xl font-semibold">{request.waste_type}</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Filed {formatDateTime(request.dispute.disputed_at)}
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-2xl bg-muted/40 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <User className="h-4 w-4 text-primary" aria-hidden="true" />
              <span>Citizen</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{request.citizen_name}</p>
          </div>
          <div className="rounded-2xl bg-muted/40 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Truck className="h-4 w-4 text-primary" aria-hidden="true" />
              <span>Collector</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {request.assigned_collector_name ?? "Not assigned"}
            </p>
          </div>
          <div className="rounded-2xl bg-muted/40 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Scale className="h-4 w-4 text-primary" aria-hidden="true" />
              <span>Weight</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Estimated: {estimated !== null && estimated !== undefined ? formatWeight(estimated) : "Not available"}
            </p>
            <p className="text-sm text-muted-foreground">
              Collector: {collectorWeight !== null && collectorWeight !== undefined ? formatWeight(collectorWeight) : "Not available"}
            </p>
            {diff !== null && (
              <p className="mt-1 text-sm font-medium text-foreground">
                Difference: {formatWeight(diff)}
              </p>
            )}
          </div>
        </div>

        <div className="rounded-2xl bg-muted/40 p-4">
          <p className="text-sm font-medium text-foreground">Dispute reason</p>
          <p className="mt-1 text-sm text-muted-foreground">{request.dispute.reason}</p>
        </div>

        {request.image_url ? (
          <img
            src={request.image_url}
            alt={`Waste image for ${request.waste_type} pickup request`}
            className="h-28 w-full rounded-2xl object-cover lg:w-40"
          />
        ) : null}

        <div className="flex flex-wrap gap-3 pt-2">
          <Button
            type="button"
            disabled={isPending}
            onClick={() => onUphold(request.id)}
          >
            Uphold Weight
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={isPending}
            onClick={() => onCorrect(request.id)}
          >
            Correct Weight
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
