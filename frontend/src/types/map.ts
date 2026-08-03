import type { PickupRequest, PickupStatus } from "@/types/pickup";

export interface CollectorLocation {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  updated_at: string;
}

export interface CollectorLocationUpdatePayload {
  latitude: number;
  longitude: number;
  accuracy?: number | null;
}

export interface PickupMarker {
  id: number;
  status: PickupStatus;
  waste_type: string;
  address: string;
  latitude: number;
  longitude: number;
  distance_km: number | null;
  eta_minutes: number | null;
}

export interface RouteGeometryPoint {
  latitude: number;
  longitude: number;
}

export interface RouteStop {
  pickup_id: number;
  order: number;
  status: PickupStatus;
  address: string;
  waste_type: string;
  latitude: number;
  longitude: number;
  distance_from_previous_km: number;
  eta_minutes: number;
}

export interface RouteSummary {
  stops: RouteStop[];
  total_distance_km: number;
  total_duration_minutes: number;
  origin_latitude: number | null;
  origin_longitude: number | null;
}

export interface NearbyPickup extends PickupRequest {
  distance_km: number;
}

export interface CollectorMapPayload {
  collector: CollectorLocation | null;
  pickups: PickupMarker[];
  route: RouteSummary | null;
  nearby_pickups: NearbyPickup[];
  radius_km: number;
}

export interface Navigation {
  pickup: PickupRequest;
  distance_km: number;
  duration_minutes: number;
  origin_latitude: number;
  origin_longitude: number;
  geometry: RouteGeometryPoint[];
}

export interface MapCoordinates {
  latitude: number;
  longitude: number;
}