import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createDealerProfile,
  getDealerProfile,
  getDealerProfileTimeline,
  submitDealerProfile,
  updateDealerProfile,
} from "@/api/dealer";
import type {
  DealerProfilePayload,
  DealerProfileUpdatePayload,
} from "@/types/dealer";

export const dealerProfileKeys = {
  all: ["dealerProfile"] as const,
  detail: () => [...dealerProfileKeys.all, "detail"] as const,
  timeline: () => [...dealerProfileKeys.all, "timeline"] as const,
};

export function useDealerProfile() {
  return useQuery({
    queryKey: dealerProfileKeys.detail(),
    queryFn: getDealerProfile,
    meta: { suppressGlobalError: true },
  });
}

export function useDealerProfileTimeline() {
  return useQuery({
    queryKey: dealerProfileKeys.timeline(),
    queryFn: getDealerProfileTimeline,
    meta: { suppressGlobalError: true },
  });
}

export function useCreateDealerProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DealerProfilePayload) => createDealerProfile(data),
    onSuccess: (profile) => {
      queryClient.setQueryData(dealerProfileKeys.detail(), profile);
      queryClient.invalidateQueries({
        queryKey: dealerProfileKeys.timeline(),
      });
    },
  });
}

export function useUpdateDealerProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DealerProfileUpdatePayload) => updateDealerProfile(data),
    onSuccess: (profile) => {
      queryClient.setQueryData(dealerProfileKeys.detail(), profile);
      queryClient.invalidateQueries({
        queryKey: dealerProfileKeys.timeline(),
      });
    },
  });
}

export function useSubmitDealerProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => submitDealerProfile(),
    onSuccess: (profile) => {
      queryClient.setQueryData(dealerProfileKeys.detail(), profile);
      queryClient.invalidateQueries({
        queryKey: dealerProfileKeys.timeline(),
      });
    },
  });
}
