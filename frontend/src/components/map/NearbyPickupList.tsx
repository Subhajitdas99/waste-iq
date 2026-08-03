import { ArrowRight, MapPin, Package } from "lucide-react";
import type { NearbyPickup } from "@/types/map";
import { formatDistanceKm } from "@/lib/map";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";

interface NearbyPickupListProps {
  pickups: NearbyPickup[];
  isFetching: boolean;
  onNavigate: (pickupId: number) => void;
}

export function NearbyPickupList({ pickups, isFetching, onNavigate }: NearbyPickupListProps) {
  if (isFetching && pickups.length === 0) {
    return <p className="px-4 py-3 text-xs text-muted-foreground">Scanning nearby pickups...</p>;
  }

  if (pickups.length === 0) {
    return (
      <EmptyState
        title="No pickups nearby"
        description="New pickup requests reported within a 5 km radius will appear here."
        className="py-6"
      />
    );
  }

  return (
    <ul className="divide-y divide-border/60" data-testid="nearby-pickups">
      {pickups.map((pickup) => (
        <li key={pickup.id} className="flex flex-wrap items-center gap-2 py-2.5 sm:flex-nowrap">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
            <Package className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{pickup.waste_type}</p>
            <p className="flex items-center gap-1 truncate text-xs text-muted-foreground">
              <MapPin className="h-3 w-3 shrink-0" />
              {pickup.address}
            </p>
          </div>
          <span
            className="text-xs tabular-nums text-muted-foreground"
            data-testid={`nearby-distance-${pickup.id}`}
          >
            {formatDistanceKm(pickup.distance_km)}
          </span>
          <span
            className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium capitalize"
            data-testid={`nearby-status-${pickup.id}`}
          >
            {pickup.status.replace(/_/g, " ")}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="gap-1 px-1.5"
            onClick={() => onNavigate(pickup.id)}
            data-testid={`nearby-navigate-${pickup.id}`}
          >
            Navigate
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </li>
      ))}
    </ul>
  );
}