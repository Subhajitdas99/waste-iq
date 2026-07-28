import api from "@/api/axios";
import type { CollectorSummary } from "@/types/pickup";

export async function getCollectorSummary(): Promise<CollectorSummary> {
  const response = await api.get<CollectorSummary>("/collector/summary");
  return response.data;
}
