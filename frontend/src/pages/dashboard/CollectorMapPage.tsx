import { useCallback, useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { LocateFixed, Package, RefreshCcw } from "lucide-react";
import { SeoHead } from "@/components/seo/SeoHead";
import { PageHeader } from "@/components/PageHeader";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import { CollectorMap } from "@/components/map/CollectorMap";
import { LocationStatus } from "@/components/map/LocationStatus";
import { NearbyPickupList } from "@/components/map/NearbyPickupList";
import { NavigationPanel } from "@/components/map/NavigationPanel";
import { RouteSummaryCard } from "@/components/map/RouteSummaryCard";
import {
  useCollectorLocation,
  useCollectorMap,
  useCollectorNavigation,
  useCollectorRoute,
  useNearbyPickups,
  useUpdateCollectorLocation,
} from "@/hooks/useCollectorMap";
import { useBrowserGeolocation } from "@/hooks/useBrowserGeolocation";
import { getApiErrorMessage } from "@/lib/api-error";

function isForbiddenError(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 403;
}

function formatRoute(route: { total_distance_km: number; total_duration_minutes: number }): string {
  return `${route.total_distance_km.toFixed(2)} km \u00b7 ${route.total_duration_minutes} min`;
}

export function CollectorMapPage() {
  const mapQuery = useCollectorMap();
  const locationQuery = useCollectorLocation();
  const routeQuery = useCollectorRoute();
  const nearbyQuery = useNearbyPickups();
  const updateLocation = useUpdateCollectorLocation();
  const { position, error: geoError, requestLocation } = useBrowserGeolocation();

  const [selectedPickupId, setSelectedPickupId] = useState<number | null>(null);
  const [navigationPickupId, setNavigationPickupId] = useState<number | null>(null);
  const navigationQuery = useCollectorNavigation(navigationPickupId);

  const payload = mapQuery.data;
  const location = payload?.collector ?? null;
  const pickups = payload?.pickups ?? [];
  const route = routeQuery.data ?? null;
  const nearby = nearbyQuery.data ?? [];
  const isFetching =
    mapQuery.isFetching || routeQuery.isFetching || nearbyQuery.isFetching || locationQuery.isFetching;

  useEffect(() => {
    if (position) {
      updateLocation.mutate({
        latitude: position.latitude,
        longitude: position.longitude,
      });
    }
  }, [position, updateLocation]);

  const submitPosition = (latitude: number, longitude: number) => {
    updateLocation.mutate({ latitude, longitude });
  };

  const handleUseMyLocation = () => {
    if (position) {
      submitPosition(position.latitude, position.longitude);
    } else {
      requestLocation();
    }
  };

  const refresh = useCallback(() => {
    void mapQuery.refetch();
    void routeQuery.refetch();
    void nearbyQuery.refetch();
    void locationQuery.refetch();
  }, [mapQuery, routeQuery, nearbyQuery, locationQuery]);

  const mapIsLoading = mapQuery.isPending && !payload;

  const stats = pickups.reduce(
    (acc, pickup) => {
      if (pickup.status === "pending") acc.pending += 1;
      if (pickup.status === "accepted" || pickup.status === "on_the_way") acc.active += 1;
      return acc;
    },
    { pending: 0, active: 0 },
  );

  return (
    <>
      <SeoHead
        title="Live Map & Route Tracking"
        description="Follow your collector's live position, active route, and nearby pickup requests."
        path="/collector/map"
      />

      <PageHeader
        title="Live Map & Route Tracking"
        description="Track your current position, sequenced route, and nearby pickup requests in real time."
        actions={
          <>
            <Button
              type="button"
              variant="outline"
              className="gap-2"
              disabled={isFetching}
              onClick={handleUseMyLocation}
            >
              <LocateFixed className="h-4 w-4" />
              {isFetching ? "Updating..." : "Use my location"}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="gap-2"
              disabled={isFetching}
              onClick={refresh}
              data-testid="refresh-map"
            >
              <RefreshCcw className="h-4 w-4" />
              {isFetching ? "Refreshing..." : "Refresh"}
            </Button>
          </>
        }
      />

      {geoError ? (
        <div
          role="alert"
          className="mb-4 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
        >
          {geoError}
        </div>
      ) : null}

      {mapQuery.isError ? (
        <DashboardCard title="Live Map">
          <div
            role="alert"
            className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            {isForbiddenError(mapQuery.error)
              ? "You do not have permission to view the collector live map. Contact an administrator if you believe this is a mistake."
              : getApiErrorMessage(mapQuery.error, "Unable to load the live map. Please try again.")}
          </div>
        </DashboardCard>
      ) : mapIsLoading ? (
        <LoadingSkeleton variant="detail" />
      ) : (
        <section className="space-y-6">
          {payload && (
            <DashboardCard
              title="Collector Map"
              description="Position and pickup markers are projected onto an auto-fitting grid. Click a marker to select it."
            >
              <CollectorMap
                location={location}
                pickups={pickups}
                route={route}
                selectedPickupId={selectedPickupId}
                onSelectPickup={setSelectedPickupId}
              />
            </DashboardCard>
          )}

          {navigationQuery.data && navigationPickupId !== null && (
            <NavigationPanel
              pickupId={navigationPickupId}
              pickupLabel={navigationQuery.data.pickup.waste_type}
              data={navigationQuery.data}
              onClose={() => setNavigationPickupId(null)}
            />
          )}

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <DashboardCard
                title="Active Route"
                description="Sequenced collection route with estimated travel time."
                actions={
                  route ? (
                    <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                      {formatRoute(route)}
                    </span>
                  ) : null
                }
              >
                <RouteSummaryCard
                  route={route}
                  isFetching={routeQuery.isFetching}
                  onNavigate={setNavigationPickupId}
                />
              </DashboardCard>

              <DashboardCard
                title="Nearby Pickup Requests"
                description="Pending requests reported within the active search radius, ordered by distance."
              >
                <NearbyPickupList
                  pickups={nearby}
                  isFetching={nearbyQuery.isFetching}
                  onNavigate={setNavigationPickupId}
                />
              </DashboardCard>
            </div>

            <aside className="space-y-6">
              <DashboardCard
                title="Location Status"
                description="Your latest reported position drives route calculations."
                actions={
                  location ? (
                    <span
                      className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
                      data-testid="location-live-badge"
                    >
                      <Package className="h-3 w-3" />
                      Live
                    </span>
                  ) : null
                }
              >
                <LocationStatus
                  location={location}
                  isFetching={locationQuery.isFetching}
                  isLoading={locationQuery.isLoading}
                  isUpdating={updateLocation.isPending}
                  updateError={updateLocation.error}
                  onUseMyLocation={handleUseMyLocation}
                />
              </DashboardCard>

              <DashboardCard
                title="Queue Snapshot"
                description="Marker counts for the current map view."
              >
                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="rounded-xl border border-border/60 p-3">
                    <p className="text-2xl font-bold text-amber-500">{stats.pending}</p>
                    <p className="text-xs font-medium text-muted-foreground">Pending</p>
                  </div>
                  <div className="rounded-xl border border-border/60 p-3">
                    <p className="text-2xl font-bold text-primary">{stats.active}</p>
                    <p className="text-xs font-medium text-muted-foreground">Active Jobs</p>
                  </div>
                </div>
              </DashboardCard>
            </aside>
          </div>
        </section>
      )}
    </>
  );
}