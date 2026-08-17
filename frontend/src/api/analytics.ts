import apiClient from "@/api/client";
import type {
  AnalyticsInsight,
  AnalyticsOverview,
  CarbonSavings,
  CollectorPerformance,
  DealerPerformance,
  MaterialBreakdown,
  MonthlyStat,
} from "@/types/analytics";

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  const response = await apiClient.get<AnalyticsOverview>("/admin/analytics/overview");
  return response.data;
}

export async function getMaterialBreakdown(): Promise<MaterialBreakdown> {
  const response = await apiClient.get<MaterialBreakdown>("/admin/analytics/materials");
  return response.data;
}

export async function getMonthlyAnalytics(): Promise<MonthlyStat[]> {
  const response = await apiClient.get<MonthlyStat[]>("/admin/analytics/monthly");
  return response.data;
}

export async function getCollectorPerformance(): Promise<CollectorPerformance[]> {
  const response = await apiClient.get<CollectorPerformance[]>("/admin/analytics/collectors");
  return response.data;
}

export async function getDealerPerformance(): Promise<DealerPerformance[]> {
  const response = await apiClient.get<DealerPerformance[]>("/admin/analytics/dealers");
  return response.data;
}

export async function getCarbonSavings(): Promise<CarbonSavings> {
  const response = await apiClient.get<CarbonSavings>("/admin/analytics/carbon");
  return response.data;
}

export async function getAnalyticsInsights(): Promise<AnalyticsInsight[]> {
  const response = await apiClient.get<AnalyticsInsight[]>("/admin/analytics/insights");
  return response.data;
}
