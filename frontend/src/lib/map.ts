import type { MapCoordinates } from "@/types/map";

export interface ViewportPoint {
  x: number;
  y: number;
}

export interface ProjectionContext {
  width: number;
  height: number;
  project: (point: MapCoordinates) => ViewportPoint;
}

const MIN_SPAN_DEGREES = 0.000001;

function computeBounds(
  points: MapCoordinates[],
): { minLatitude: number; maxLatitude: number; minLongitude: number; maxLongitude: number } | null {
  if (points.length === 0) {
    return null;
  }

  return points.reduce(
    (bounds, point) => ({
      minLatitude: Math.min(bounds.minLatitude, point.latitude),
      maxLatitude: Math.max(bounds.maxLatitude, point.latitude),
      minLongitude: Math.min(bounds.minLongitude, point.longitude),
      maxLongitude: Math.max(bounds.maxLongitude, point.longitude),
    }),
    {
      minLatitude: points[0].latitude,
      maxLatitude: points[0].latitude,
      minLongitude: points[0].longitude,
      maxLongitude: points[0].longitude,
    },
  );
}

/**
 * Builds an equirectangular projection that fits every point inside the viewport
 * (with padding). When all points share one coordinate, the span collapses to
 * `MIN_SPAN_DEGREES` so a single collector still renders at the centre.
 */
export function createProjection(
  points: MapCoordinates[],
  viewportWidth: number,
  viewportHeight: number,
  padding = 40,
): ProjectionContext {
  const width = Math.max(viewportWidth, 1);
  const height = Math.max(viewportHeight, 1);
  const innerWidth = Math.max(width - padding * 2, 1);
  const innerHeight = Math.max(height - padding * 2, 1);

  const bounds = computeBounds(points) ?? {
    minLatitude: 0,
    maxLatitude: 0,
    minLongitude: 0,
    maxLongitude: 0,
  };

  const spanLongitude = Math.max(bounds.maxLongitude - bounds.minLongitude, MIN_SPAN_DEGREES);
  const spanLatitude = Math.max(bounds.maxLatitude - bounds.minLatitude, MIN_SPAN_DEGREES);
  const scale = Math.min(innerWidth / spanLongitude, innerHeight / spanLatitude);

  const centerLongitude = (bounds.minLongitude + bounds.maxLongitude) / 2;
  const centerLatitude = (bounds.minLatitude + bounds.maxLatitude) / 2;

  const project = (point: MapCoordinates): ViewportPoint => ({
    x: width / 2 + (point.longitude - centerLongitude) * scale,
    y: height / 2 - (point.latitude - centerLatitude) * scale,
  });

  return { width, height, project };
}

/**
 * Builds an SVG polyline "points" string for the given coordinates.
 */
export function buildPolylinePoints(
  project: ProjectionContext["project"],
  points: MapCoordinates[],
): string {
  return points.map((point) => {
    const { x, y } = project(point);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

export function formatDistanceKm(distanceKm: number | null | undefined): string {
  if (typeof distanceKm !== "number") {
    return "Unknown";
  }
  return `${distanceKm.toFixed(2)} km`;
}

export function formatDurationMinutes(minutes: number | null | undefined): string {
  if (typeof minutes !== "number") {
    return "Unknown";
  }
  if (minutes < 1) {
    return "<1 min";
  }
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}