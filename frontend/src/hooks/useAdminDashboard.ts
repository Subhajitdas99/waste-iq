import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  approveAdminDealer,
  getAdminAnalytics,
  getPilotMetrics,
  listAdminDealers,
  listAdminUsers,
  listPendingAdminDealers,
  rejectAdminDealer,
} from "@/api/admin";
import type { AdminDealerListQuery } from "@/types/admin";

export const adminDashboardQueryKeys = {
  all: ["admin"] as const,
  analytics: ["admin", "analytics"] as const,
  pilot: ["admin", "analytics", "pilot"] as const,
  users: ["admin", "users"] as const,
  dealers: ["admin", "dealers"] as const,
  dealerList: (query: AdminDealerListQuery = {}) =>
    [...adminDashboardQueryKeys.dealers, query] as const,
  pendingDealers: (query: AdminDealerListQuery = {}) =>
    [...adminDashboardQueryKeys.dealers, "pending", query] as const,
};

export function useAdminAnalytics() {
  return useQuery({
    queryKey: adminDashboardQueryKeys.analytics,
    queryFn: getAdminAnalytics,
  });
}

export function usePilotMetrics() {
  return useQuery({
    queryKey: adminDashboardQueryKeys.pilot,
    queryFn: getPilotMetrics,
  });
}

export function useAdminUsers() {
  return useQuery({
    queryKey: adminDashboardQueryKeys.users,
    queryFn: listAdminUsers,
  });
}

export function useAdminDealers(query: AdminDealerListQuery = {}) {
  return useQuery({
    queryKey: adminDashboardQueryKeys.dealerList(query),
    queryFn: () => listAdminDealers(query),
  });
}

export function usePendingAdminDealers(query: AdminDealerListQuery = {}) {
  return useQuery({
    queryKey: adminDashboardQueryKeys.pendingDealers(query),
    queryFn: () => listPendingAdminDealers(query),
  });
}

export function useApproveDealer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (dealerUserId: number) => approveAdminDealer(dealerUserId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminDashboardQueryKeys.dealers,
      });
    },
  });
}

export function useRejectDealer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dealerUserId, reason }: { dealerUserId: number; reason: string }) =>
      rejectAdminDealer(dealerUserId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: adminDashboardQueryKeys.dealers,
      });
    },
  });
}
