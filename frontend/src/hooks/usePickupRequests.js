import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getAdminAnalytics, listAdminUsers } from "../api/admin";
import { approveDealer, listAdminDealers, rejectDealer } from "../api/dealers";
import {
  cancelPickupRequest,
  createPickupRequest,
  getCitizenDashboardSummary,
  getPickupRequestDetail,
  listPickupRequests
} from "../api/pickupRequests";

export const pickupRequestQueryKeys = {
  all: ["pickup-requests"],
  detail: (id) => [...pickupRequestQueryKeys.all, "detail", id],
  citizenSummary: ["citizen-summary"],
  adminAnalytics: ["admin-analytics"],
  adminUsers: ["admin-users"],
  adminDealers: ["admin-dealers"]
};

function invalidatePickupRequestQueries(queryClient) {
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.all });
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.citizenSummary });
}

function invalidateAdminQueries(queryClient) {
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.adminAnalytics });
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.adminUsers });
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.adminDealers });
}

export function useCitizenSummary() {
  return useQuery({
    queryKey: pickupRequestQueryKeys.citizenSummary,
    queryFn: getCitizenDashboardSummary
  });
}

export function usePickupRequests() {
  return useQuery({
    queryKey: pickupRequestQueryKeys.all,
    queryFn: listPickupRequests
  });
}

export function useAdminAnalytics() {
  return useQuery({
    queryKey: pickupRequestQueryKeys.adminAnalytics,
    queryFn: getAdminAnalytics
  });
}

export function useAdminUsers() {
  return useQuery({
    queryKey: pickupRequestQueryKeys.adminUsers,
    queryFn: listAdminUsers
  });
}

export function useAdminDealers() {
  return useQuery({
    queryKey: pickupRequestQueryKeys.adminDealers,
    queryFn: listAdminDealers
  });
}

export function usePickupRequest(id, options = {}) {
  return useQuery({
    queryKey: pickupRequestQueryKeys.detail(id),
    queryFn: () => getPickupRequestDetail(id),
    ...options,
    enabled: Boolean(id) && (options.enabled ?? true)
  });
}

export function useCreatePickup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPickupRequest,
    onSuccess: () => {
      invalidatePickupRequestQueries(queryClient);
    }
  });
}

export function useCancelPickup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelPickupRequest,
    onSuccess: () => {
      invalidatePickupRequestQueries(queryClient);
    }
  });
}

function useDealerAction(mutationFn) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: () => {
      invalidateAdminQueries(queryClient);
    }
  });
}

export function useApproveDealer() {
  return useDealerAction(approveDealer);
}

export function useRejectDealer() {
  return useDealerAction(rejectDealer);
}
