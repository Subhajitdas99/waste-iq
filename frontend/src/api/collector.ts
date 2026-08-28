import apiClient from "@/api/client";
import type { CollectorSummary } from "@/types/collector";
import type { PickupRequest, PickupRequestDetail } from "@/types/pickup";

export async function getCollectorSummary(): Promise<CollectorSummary> {
  const response = await apiClient.get<CollectorSummary>("/collector/summary");
  return response.data;
}

export async function listAvailableCollectorRequests(): Promise<PickupRequest[]> {
  const response = await apiClient.get<PickupRequest[]>("/collector/pickups/available");
  return response.data;
}

export async function listAssignedCollectorRequests(): Promise<PickupRequest[]> {
  const response = await apiClient.get<PickupRequest[]>("/collector/pickups/assigned");
  return response.data;
}

export async function getCollectorPickupDetail(
  requestId: number | string,
): Promise<PickupRequestDetail> {
  const response = await apiClient.get<PickupRequestDetail>(`/collector/pickups/${requestId}`);
  return response.data;
}

export async function acceptCollectorPickup(requestId: number): Promise<PickupRequest> {
  const response = await apiClient.post<PickupRequest>(`/collector/pickups/${requestId}/accept`);
  return response.data;
}

export async function startCollectorPickup(requestId: number): Promise<PickupRequest> {
  const response = await apiClient.post<PickupRequest>(`/collector/pickups/${requestId}/start`);
  return response.data;
}

export async function collectCollectorPickup(requestId: number): Promise<PickupRequest> {
  const response = await apiClient.post<PickupRequest>(`/collector/pickups/${requestId}/collect`);
  return response.data;
}

export async function recordWeightCollectorPickup(
  requestId: number,
  weightKg: number,
): Promise<PickupRequest> {
  const response = await apiClient.post<PickupRequest>(`/collector/pickups/${requestId}/record-weight`, {
    weight_kg: weightKg,
  });
  return response.data;
}

export async function completeCollectorPickup(
  requestId: number,
  weightKg: number,
): Promise<PickupRequest> {
  const response = await apiClient.post<PickupRequest>(`/collector/pickups/${requestId}/complete`, {
    weight_kg: weightKg,
  });
  return response.data;
}

export async function cancelCollectorPickup(requestId: number): Promise<PickupRequest> {
  const response = await apiClient.post<PickupRequest>(`/collector/pickups/${requestId}/cancel`);
  return response.data;
}
