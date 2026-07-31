import { useQuery } from "@tanstack/react-query";
import {
  getAdminAnalytics,
  listAdminDealers,
  listAdminUsers,
} from "@/api/admin";

export const adminDashboardQueryKeys = {
  all: ["admin"] as const,
  analytics: ["admin", "analytics"] as const,
  users: ["admin", "users"] as const,
  dealers: ["admin", "dealers"] as const,
};

export function useAdminAnalytics() {
  return useQuery({
    queryKey: adminDashboardQueryKeys.analytics,
    queryFn: getAdminAnalytics,
  });
}

export function useAdminUsers() {
  return useQuery({
    queryKey: adminDashboardQueryKeys.users,
    queryFn: listAdminUsers,
  });
}

export function useAdminDealers() {
  return useQuery({
    queryKey: adminDashboardQueryKeys.dealers,
    queryFn: listAdminDealers,
  });
}
