import { useState, type ReactNode } from "react";
import { ChevronDown, MapPin, Route, Truck } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import {
  formatDateTime,
  formatWeight,
  getPickupProgress,
} from "@/lib/pickup";
import type { PickupRequest } from "@/types/pickup";
import { cn } from "@/lib/utils";

interface PickupCardProps {
  request: PickupRequest;
  footer?: ReactNode;
  expandable?: boolean;
  defaultExpanded?: boolean;
  className?: string;
}

export function PickupCard({
  request,
  footer,
  expandable = false,
  defaultExpanded = false,
  className,
}: PickupCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const progress = getPickupProgress(request.status);

  return (
    <Card className={cn("border-white/40 bg-card/85 shadow-sm", className)}>
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-medium text-muted-foreground">
                Request #{request.id}
              </p>
              <StatusBadge status={request.status} />
            </div>
            <h3 className="mt-3 text-xl font-semibold">{request.waste_type}</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Created {formatDateTime(request.created_at)}
            </p>
          </div>

          {expandable ? (
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition hover:bg-muted"
              onClick={() => setIsExpanded((current) => !current)}
            >
              Details
              <ChevronDown
                className={cn("h-4 w-4 transition-transform", isExpanded && "rotate-180")}
              />
            </button>
          ) : null}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs uppercase tracking-[0.2em] text-muted-foreground">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 rounded-full bg-muted">
            <div
              className="h-2 rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl bg-muted/40 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <MapPin className="h-4 w-4 text-primary" />
              Address
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{request.address}</p>
          </div>
          <div className="rounded-2xl bg-muted/40 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Truck className="h-4 w-4 text-primary" />
              Collector
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {request.assigned_collector_name ?? "Awaiting assignment"}
            </p>
          </div>
          <div className="rounded-2xl bg-muted/40 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Route className="h-4 w-4 text-primary" />
              Weight
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {formatWeight(request.assignment?.weight_kg)}
            </p>
          </div>
        </div>

        {(isExpanded || !expandable) && (
          <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>
                <span className="font-medium text-foreground">Material insight:</span>{" "}
                {request.category
                  ? `${request.category}${
                      typeof request.confidence === "number"
                        ? ` (${Math.round(request.confidence * 100)}% confidence)`
                        : ""
                    }`
                  : "No AI classification returned by the backend."}
              </p>
              <p>
                <span className="font-medium text-foreground">Coordinates:</span>{" "}
                {request.latitude.toFixed(5)}, {request.longitude.toFixed(5)}
              </p>
            </div>
            {request.image_url ? (
              <img
                src={request.image_url}
                alt={request.waste_type}
                className="h-28 w-full rounded-2xl object-cover lg:w-40"
              />
            ) : null}
          </div>
        )}

        {footer ? <div className="flex flex-wrap gap-3 pt-2">{footer}</div> : null}
      </CardContent>
    </Card>
  );
}
