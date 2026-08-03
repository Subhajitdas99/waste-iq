import { Link } from "react-router-dom";
import { ArrowRight, Map, Route as RouteIcon, Timer } from "lucide-react";
import type { RouteSummary as RouteSummaryData } from "@/types/map";
import { formatDistanceKm, formatDurationMinutes } from "@/lib/map";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { EmptyState } from "@/components/EmptyState";

interface RouteSummaryProps {
  route: RouteSummaryData | null;
  isFetching: boolean;
  onNavigate: (pickupId: number) => void;
}

export function RouteSummaryCard({ route, isFetching, onNavigate }: RouteSummaryProps) {
  if (isFetching && !route) {
    return <p className="px-4 py-3 text-xs text-muted-foreground">Refreshing...</p>;
  }

  if (!route || route.stops.length === 0) {
    return (
      <EmptyState
        title="No active route"
        description="Your accepted pickups will be sequenced into a route here. Assign pickups or accept requests to see a live route."
        className="py-6"
      />
    );
  }

  const orderedStops = [...route.stops].sort((a, b) => a.order - b.order);

  return (
    <div className="space-y-2" data-testid="route-summary">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-1 font-medium text-primary">
          <RouteIcon className="h-3 w-3" />
          {orderedStops.length} stop{orderedStops.length === 1 ? "" : "s"}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-1 font-medium">
          <Map className="h-3 w-3" />
          {formatDistanceKm(route.total_distance_km)}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-1 font-medium">
          <Timer className="h-3 w-3" />
          {formatDurationMinutes(route.total_duration_minutes)}
        </span>
        {isFetching ? <span className="italic">updating...</span> : null}
      </div>

      <ol className="divide-y divide-border/60">
        {orderedStops.map((stop, index) => (
          <li key={stop.pickup_id} className="flex flex-wrap items-center gap-2 py-2 sm:flex-nowrap">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
              {index + 1}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium">{stop.waste_type}</span>
              <span className="block truncate text-xs text-muted-foreground">{stop.address}</span>
            </span>
            <span className="text-xs tabular-nums text-muted-foreground">
              {stop.eta_minutes} min ETA
            </span>
            <StatusBadge status={stop.status} />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="gap-1 px-1.5"
              onClick={() => onNavigate(stop.pickup_id)}
              data-testid={`route-navigate-${stop.pickup_id}`}
            >
              Navigate
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </li>
        ))}
      </ol>

      <p className="text-xs text-muted-foreground">
        <Link to="/collector/pickups" className="font-medium text-primary hover:underline">
          View all assigned pickups
        </Link>
      </p>
    </div>
  );
}