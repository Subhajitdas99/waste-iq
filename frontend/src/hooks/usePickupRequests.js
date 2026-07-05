import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getAdminAnalytics, listAdminUsers } from "../api/admin";
import { approveDealer, listAdminDealers, rejectDealer } from "../api/dealers";
import {
  acceptPickupRequest,
  cancelPickupRequest,
  collectPickupRequest,
  completePickupRequest,
  createPickupRequest,
  getCitizenDashboardSummary,
  getCollectorSummary,
  getPickupRequestDetail,
  listPickupRequests,
  startPickupRequest
} from "../api/pickupRequests";

export const pickupRequestQueryKeys = {
  all: ["pickup-requests"],
  detail: (id) => [...pickupRequestQueryKeys.all, "detail", id],
  citizenSummary: ["citizen-summary"],
  collectorSummary: ["collector-summary"],
  adminAnalytics: ["admin-analytics"],
  adminUsers: ["admin-users"],
  adminDealers: ["admin-dealers"]
};

function invalidatePickupRequestQueries(queryClient) {
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.all });
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.citizenSummary });
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.collectorSummary });
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

export function useCollectorSummary() {
  return useQuery({
    queryKey: pickupRequestQueryKeys.collectorSummary,
    queryFn: getCollectorSummary
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

export function usePickupRequest(id) {
  return useQuery({
    queryKey: pickupRequestQueryKeys.detail(id),
    queryFn: () => getPickupRequestDetail(id),
    enabled: Boolean(id)
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

function usePickupAction(mutationFn) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: () => {
      invalidatePickupRequestQueries(queryClient);
    }
  });
}

export function useAcceptPickup() {
  return usePickupAction(acceptPickupRequest);
}

export function useStartPickup() {
  return usePickupAction(startPickupRequest);
}

export function useCollectPickup() {
  return usePickupAction(collectPickupRequest);
}

export function useCompletePickup() {
  return usePickupAction(completePickupRequest);
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
