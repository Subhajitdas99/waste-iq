import { LocateFixed, MapPin } from "lucide-react";
import type { CollectorLocation } from "@/types/map";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/lib/api-error";

interface LocationStatusProps {
  location: CollectorLocation | null;
  isFetching: boolean;
  isLoading: boolean;
  isUpdating: boolean;
  updateError: unknown;
  onUseMyLocation: () => void;
}

function formatUpdatedAt(updatedAt: string | null | undefined): string {
  if (!updatedAt) {
    return "Never reported";
  }
  const date = new Date(updatedAt);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }
  return date.toLocaleString();
}

export function LocationStatus({
  location,
  isFetching,
  isLoading,
  isUpdating,
  updateError,
  onUseMyLocation,
}: LocationStatusProps) {
  return (
    <div data-testid="location-status">
      <div className="flex items-start gap-3">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <MapPin className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">Current Position</p>
          {location ? (
            <>
              <p className="mt-1 text-xs text-muted-foreground" data-testid="location-coordinates">
                {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
              </p>
              <p className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                <LocateFixed className="h-3 w-3" />
                Updated {formatUpdatedAt(location.updated_at)}
              </p>
            </>
          ) : (
            <p className="mt-1 text-xs text-muted-foreground" data-testid="location-missing">
              {isLoading ? "Checking your last reported location..." : "No location reported yet."}
            </p>
          )}
          {isUpdating ? (
            <p className="mt-1 text-xs font-medium text-primary">Updating location...</p>
          ) : null}
          {isFetching ? (
            <p className="mt-1 text-xs text-muted-foreground">Refreshing...</p>
          ) : null}
          {updateError ? (
            <p className="mt-1 text-xs text-destructive" role="alert">
              {getApiErrorMessage(updateError, "Unable to update your location.")}
            </p>
          ) : null}
        </div>
      </div>

      <Button
        type="button"
        variant="outline"
        size="sm"
        className="mt-3 gap-1.5"
        onClick={onUseMyLocation}
        disabled={isUpdating}
        data-testid="use-my-location"
      >
        <LocateFixed className="h-4 w-4" />
        {isLoading || isUpdating ? "Locating..." : "Use my location"}
      </Button>
    </div>
  );
}