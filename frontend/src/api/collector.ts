import apiClient from "@/api/client";
import type { CollectorSummary } from "@/types/collector";
import type { PickupRequest } from "@/types/pickup";

export async function getCollectorSummary(): Promise<CollectorSummary> {
  const response = await apiClient.get<CollectorSummary>("/collector/summary");
  return response.data;
}

export async function listAvailableCollectorRequests(): Promise<PickupRequest[]> {
  const response = await apiClient.get<PickupRequest[]>("/collector/available");
  return response.data;
}
