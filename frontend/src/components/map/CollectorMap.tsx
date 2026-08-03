import { useMemo, useState } from "react";
import { LocateFixed } from "lucide-react";
import type { CollectorLocation, PickupMarker as PickupMarkerData, RouteSummary } from "@/types/map";
import type { MapCoordinates } from "@/types/map";
import { buildPolylinePoints, createProjection } from "@/lib/map";
import { Button } from "@/components/ui/button";
import { CollectorMarker } from "./CollectorMarker";
import { PickupMarker as PickupMarkerComponent } from "./PickupMarker";

const MAP_VIEWBOX_WIDTH = 800;
const MAP_VIEWBOX_HEIGHT = 420;
const ROUTE_STROKE_COLOR = "#6366f1";

interface CollectorMapProps {
  location: CollectorLocation | null;
  pickups: PickupMarkerData[];
  route: RouteSummary | null;
  selectedPickupId: number | null;
  onSelectPickup: (pickupId: number | null) => void;
}

function routePointsFor(route: RouteSummary | null, location: CollectorLocation | null): MapCoordinates[] {
  const points: MapCoordinates[] = [];
  if (!route) {
    return points;
  }
  if (route.origin_latitude != null && route.origin_longitude != null) {
    points.push({ latitude: route.origin_latitude, longitude: route.origin_longitude });
  } else if (location) {
    points.push({ latitude: location.latitude, longitude: location.longitude });
  }
  const orderedStops = [...route.stops]
    .sort((a, b) => a.order - b.order)
    .map((stop) => ({ latitude: stop.latitude, longitude: stop.longitude }));
  points.push(...orderedStops);
  return points;
}

export function CollectorMap({
  location,
  pickups,
  route,
  selectedPickupId,
  onSelectPickup,
}: CollectorMapProps) {
  const [fitVersion, setFitVersion] = useState(0);

  const dataPoints: MapCoordinates[] = useMemo(() => {
    const points: MapCoordinates[] = [];
    if (location) {
      points.push({ latitude: location.latitude, longitude: location.longitude });
    }
    for (const pickup of pickups) {
      points.push({ latitude: pickup.latitude, longitude: pickup.longitude });
    }
    return points;
  }, [location, pickups]);

  const projection = useMemo(
    () =>
      createProjection(dataPoints, MAP_VIEWBOX_WIDTH, MAP_VIEWBOX_HEIGHT, 48),
    // fitVersion exists so the "Recenter" button re-runs the fit with fresh padding.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [dataPoints, fitVersion],
  );

  const routePoints = routePointsFor(route, location);
  const routePolyline = buildPolylinePoints(projection.project, routePoints);

  const recenter = () => setFitVersion((version) => version + 1);

  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-white/40 bg-muted/20">
      <svg
        viewBox={`0 0 ${MAP_VIEWBOX_WIDTH} ${MAP_VIEWBOX_HEIGHT}`}
        role="img"
        aria-label="Collector live map"
        className="h-auto w-full"
        data-testid="collector-map"
      >
        <defs>
          <pattern id="map-grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148,163,184,0.18)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={MAP_VIEWBOX_WIDTH} height={MAP_VIEWBOX_HEIGHT} fill="url(#map-grid-pattern)" />

        {route && routePoints.length > 1 && (
          <g data-testid="route-overlay">
            <polyline
              points={routePolyline}
              fill="none"
              stroke="rgba(255,255,255,0.95)"
              strokeWidth={7}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <polyline
              points={routePolyline}
              fill="none"
              stroke={ROUTE_STROKE_COLOR}
              strokeWidth={3}
              strokeLinecap="round"
              strokeLinejoin="round"
              data-testid="route-polyline"
            />
          </g>
        )}

        {location && (
          <CollectorMarker
            x={projection.project(location).x}
            y={projection.project(location).y}
            accuracy={location.accuracy}
            active
          />
        )}

        {pickups.map((pickup) => {
          const { x, y } = projection.project(pickup);
          return (
            <PickupMarkerComponent
              key={pickup.id}
              id={pickup.id}
              status={pickup.status}
              x={x}
              y={y}
              label={pickup.waste_type.slice(0, 3).toUpperCase()}
              active={pickup.id === selectedPickupId}
              isActivePickup={pickup.status === "on_the_way" || pickup.status === "accepted"}
              onClick={onSelectPickup}
            />
          );
        })}
      </svg>

      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={recenter}
        className="absolute bottom-3 left-3 gap-1.5 bg-background/90 backdrop-blur"
        data-testid="recenter-map"
      >
        <LocateFixed className="h-4 w-4" />
        Recenter
      </Button>

      {location && (
        <div
          className="pointer-events-none absolute bottom-3 right-3 rounded-full bg-background/90 px-3 py-1.5 text-xs font-medium text-muted-foreground backdrop-blur"
          data-testid="map-location-coords"
        >
          {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
        </div>
      )}
    </div>
  );
}