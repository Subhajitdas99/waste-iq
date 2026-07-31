import { useQuery } from "@tanstack/react-query";
import {
  getAnalyticsInsights,
  getAnalyticsOverview,
  getCarbonSavings,
  getCollectorPerformance,
  getDealerPerformance,
  getMaterialBreakdown,
  getMonthlyAnalytics,
} from "@/api/analytics";

export const analyticsQueryKeys = {
  all: ["admin", "analytics"] as const,
  overview: ["admin", "analytics", "overview"] as const,
  materials: ["admin", "analytics", "materials"] as const,
  monthly: ["admin", "analytics", "monthly"] as const,
  collectors: ["admin", "analytics", "collectors"] as const,
  dealers: ["admin", "analytics", "dealers"] as const,
  carbon: ["admin", "analytics", "carbon"] as const,
  insights: ["admin", "analytics", "insights"] as const,
};

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: analyticsQueryKeys.overview,
    queryFn: getAnalyticsOverview,
  });
}

export function useMaterialBreakdown() {
  return useQuery({
    queryKey: analyticsQueryKeys.materials,
    queryFn: getMaterialBreakdown,
  });
}

export function useMonthlyAnalytics() {
  return useQuery({
    queryKey: analyticsQueryKeys.monthly,
    queryFn: getMonthlyAnalytics,
  });
}

export function useCollectorPerformance() {
  return useQuery({
    queryKey: analyticsQueryKeys.collectors,
    queryFn: getCollectorPerformance,
  });
}

export function useDealerPerformance() {
  return useQuery({
    queryKey: analyticsQueryKeys.dealers,
    queryFn: getDealerPerformance,
  });
}

export function useCarbonSavings() {
  return useQuery({
    queryKey: analyticsQueryKeys.carbon,
    queryFn: getCarbonSavings,
  });
}

export function useAnalyticsInsights() {
  return useQuery({
    queryKey: analyticsQueryKeys.insights,
    queryFn: getAnalyticsInsights,
  });
}
