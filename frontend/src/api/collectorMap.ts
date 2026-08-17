import apiClient from "@/api/client";
import type {
  CollectorLocation,
  CollectorLocationUpdatePayload,
  CollectorMapPayload,
  Navigation,
  NearbyPickup,
  RouteSummary,
} from "@/types/map";

export interface CollectorMapParams {
  latitude?: number;
  longitude?: number;
  radiusKm?: number;
}

export async function getCollectorMap(
  params: CollectorMapParams = {},
): Promise<CollectorMapPayload> {
  const response = await apiClient.get<CollectorMapPayload>("/collector/map", {
    params: {
      latitude: params.latitude,
      longitude: params.longitude,
      radius_km: params.radiusKm,
    },
  });
  return response.data;
}

export async function getCollectorLocation(): Promise<CollectorLocation> {
  const response = await apiClient.get<CollectorLocation>("/collector/location");
  return response.data;
}

export async function updateCollectorLocation(
  payload: CollectorLocationUpdatePayload,
): Promise<CollectorLocation> {
  const response = await apiClient.post<CollectorLocation>("/collector/location", payload);
  return response.data;
}

export async function getCollectorRoute(
  params: { latitude?: number; longitude?: number } = {},
): Promise<RouteSummary> {
  const response = await apiClient.get<RouteSummary>("/collector/route", {
    params: {
      latitude: params.latitude,
      longitude: params.longitude,
    },
  });
  return response.data;
}

export async function listNearbyPickups(
  params: { latitude?: number; longitude?: number; radiusKm?: number } = {},
): Promise<NearbyPickup[]> {
  const response = await apiClient.get<NearbyPickup[]>("/collector/nearby-pickups", {
    params: {
      latitude: params.latitude,
      longitude: params.longitude,
      radius_km: params.radiusKm,
    },
  });
  return response.data;
}

export async function getCollectorNavigation(
  pickupId: number,
  params: { latitude?: number; longitude?: number } = {},
): Promise<Navigation> {
  const response = await apiClient.get<Navigation>(`/collector/navigation/${pickupId}`, {
    params: {
      latitude: params.latitude,
      longitude: params.longitude,
    },
  });
  return response.data;
}