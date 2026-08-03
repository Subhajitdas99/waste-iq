import { Link } from "react-router-dom";
import { Clock, MapPin, Navigation, X } from "lucide-react";
import type { Navigation as NavigationResult } from "@/types/map";
import { buildPolylinePoints, createProjection, formatDistanceKm, formatDurationMinutes } from "@/lib/map";
import type { MapCoordinates } from "@/types/map";
import { Button } from "@/components/ui/button";

const VIEWBOX_WIDTH = 800;
const VIEWBOX_HEIGHT = 180;

interface NavigationPanelProps {
  pickupId: number;
  pickupLabel: string;
  data: NavigationResult;
  onClose: () => void;
}

export function NavigationPanel({ pickupId, pickupLabel, data, onClose }: NavigationPanelProps) {
  const points: MapCoordinates[] = [
    { latitude: data.origin_latitude, longitude: data.origin_longitude },
    ...data.geometry,
    { latitude: data.pickup.latitude, longitude: data.pickup.longitude },
  ];

  const projection = createProjection(points, VIEWBOX_WIDTH, VIEWBOX_HEIGHT, 24);
  const polyline = buildPolylinePoints(projection.project, points);
  const destination = projection.project({
    latitude: data.pickup.latitude,
    longitude: data.pickup.longitude,
  });

  const path = polyline
    .split(" ")
    .map((point, index) => {
      const [x, y] = point.split(",").map(Number);
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  return (
    <div
      className="overflow-hidden rounded-2xl border border-primary/30 bg-background"
      data-testid="navigation-panel"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold">Navigation to {pickupLabel}</p>
          <p className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <Navigation className="h-3 w-3" />
              {formatDistanceKm(data.distance_km)}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDurationMinutes(data.duration_minutes)}
            </span>
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="gap-1 px-2"
          onClick={onClose}
          data-testid="close-navigation"
        >
          <X className="h-4 w-4" />
          Close
        </Button>
      </div>

      <svg
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        className="h-auto w-full bg-muted/20"
        data-testid="navigation-map"
      >
        <path
          d={path}
          fill="none"
          stroke="#6366f1"
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
          data-testid="navigation-polyline"
        />
        <circle
          cx={destination.x}
          cy={destination.y}
          r={6}
          fill="#10b981"
          stroke="white"
          strokeWidth={2}
          data-testid="navigation-destination"
        />
      </svg>

      <div className="flex items-center justify-between gap-2 px-4 py-3">
        <div className="flex min-w-0 items-start gap-2 text-xs text-muted-foreground">
          <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span className="min-w-0 truncate">{data.pickup.address}</span>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to={`/collector/pickups/${pickupId}`}>View Details</Link>
        </Button>
      </div>
    </div>
  );
}