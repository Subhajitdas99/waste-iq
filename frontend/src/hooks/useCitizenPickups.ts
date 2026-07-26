import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  cancelPickupRequest,
  createPickupRequest,
  getCitizenRequestSummary,
  getPickupRequestDetail,
  listPickupRequests,
  updatePickupRequest,
} from "@/api/pickupRequests";
import type {
  CitizenRequestSummary,
  CreatePickupRequestPayload,
  PickupRequest,
  PickupRequestDetail,
  PickupRequestUpdatePayload,
} from "@/types/pickup";

export const citizenPickupQueryKeys = {
  all: ["citizen-pickups"] as const,
  summary: ["citizen-pickups", "summary"] as const,
  detail: (requestId: number | string) => ["citizen-pickups", "detail", requestId] as const,
};

interface CreatePickupMutationInput {
  payload: CreatePickupRequestPayload;
  onUploadProgress?: (progress: number) => void;
}

interface UpdatePickupMutationInput {
  requestId: number;
  payload: PickupRequestUpdatePayload;
}

interface CancelMutationContext {
  previousRequests?: PickupRequest[];
  previousSummary?: CitizenRequestSummary;
  previousDetail?: PickupRequestDetail;
}

export function useCitizenPickupSummary() {
  return useQuery({
    queryKey: citizenPickupQueryKeys.summary,
    queryFn: getCitizenRequestSummary,
  });
}

export function useCitizenPickups() {
  return useQuery({
    queryKey: citizenPickupQueryKeys.all,
    queryFn: listPickupRequests,
  });
}

export function useCitizenPickupDetail(requestId: number | string) {
  return useQuery({
    queryKey: citizenPickupQueryKeys.detail(requestId),
    queryFn: () => getPickupRequestDetail(requestId),
    enabled: Boolean(requestId),
  });
}

export function useCreateCitizenPickup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ payload, onUploadProgress }: CreatePickupMutationInput) =>
      createPickupRequest(payload, onUploadProgress),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: citizenPickupQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: citizenPickupQueryKeys.summary }),
      ]);
    },
  });
}

export function useUpdateCitizenPickup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ requestId, payload }: UpdatePickupMutationInput) =>
      updatePickupRequest(requestId, payload),
    onSuccess: async (_, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: citizenPickupQueryKeys.all }),
        queryClient.invalidateQueries({
          queryKey: citizenPickupQueryKeys.detail(variables.requestId),
        }),
      ]);
    },
  });
}

export function useCancelCitizenPickup() {
  const queryClient = useQueryClient();

  return useMutation<PickupRequest, Error, number, CancelMutationContext>({
    mutationFn: cancelPickupRequest,
    onMutate: async (requestId) => {
      await Promise.all([
        queryClient.cancelQueries({ queryKey: citizenPickupQueryKeys.all }),
        queryClient.cancelQueries({ queryKey: citizenPickupQueryKeys.summary }),
        queryClient.cancelQueries({ queryKey: citizenPickupQueryKeys.detail(requestId) }),
      ]);

      const previousRequests = queryClient.getQueryData<PickupRequest[]>(
        citizenPickupQueryKeys.all,
      );
      const previousSummary = queryClient.getQueryData<CitizenRequestSummary>(
        citizenPickupQueryKeys.summary,
      );
      const previousDetail = queryClient.getQueryData<PickupRequestDetail>(
        citizenPickupQueryKeys.detail(requestId),
      );

      if (previousRequests) {
        queryClient.setQueryData<PickupRequest[]>(
          citizenPickupQueryKeys.all,
          previousRequests.map((request) =>
            request.id === requestId
              ? { ...request, status: "cancelled", can_cancel: false }
              : request,
          ),
        );
      }

      if (previousSummary && previousSummary.pending_requests > 0) {
        queryClient.setQueryData<CitizenRequestSummary>(citizenPickupQueryKeys.summary, {
          ...previousSummary,
          pending_requests: previousSummary.pending_requests - 1,
        });
      }

      if (previousDetail) {
        queryClient.setQueryData<PickupRequestDetail>(
          citizenPickupQueryKeys.detail(requestId),
          {
            ...previousDetail,
            status: "cancelled",
            can_cancel: false,
          },
        );
      }

      return { previousRequests, previousSummary, previousDetail };
    },
    onError: (_error, requestId, context) => {
      if (context?.previousRequests) {
        queryClient.setQueryData(citizenPickupQueryKeys.all, context.previousRequests);
      }
      if (context?.previousSummary) {
        queryClient.setQueryData(citizenPickupQueryKeys.summary, context.previousSummary);
      }
      if (context?.previousDetail) {
        queryClient.setQueryData(
          citizenPickupQueryKeys.detail(requestId),
          context.previousDetail,
        );
      }
    },
    onSettled: async (_data, _error, requestId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: citizenPickupQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: citizenPickupQueryKeys.summary }),
        queryClient.invalidateQueries({
          queryKey: citizenPickupQueryKeys.detail(requestId),
        }),
      ]);
    },
  });
}
