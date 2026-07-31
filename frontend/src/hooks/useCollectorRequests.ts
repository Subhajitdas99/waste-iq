import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  acceptCollectorPickup,
  cancelCollectorPickup,
  collectCollectorPickup,
  completeCollectorPickup,
  getCollectorPickupDetail,
  getCollectorSummary,
  listAssignedCollectorRequests,
  listAvailableCollectorRequests,
  startCollectorPickup,
} from "@/api/collector";
import type { PickupRequest, PickupRequestDetail } from "@/types/pickup";

export const collectorQueryKeys = {
  all: ["collector"] as const,
  summary: ["collector", "summary"] as const,
  available: ["collector", "available"] as const,
  assigned: ["collector", "assigned"] as const,
  detail: (requestId: number | string) => ["collector", "pickups", requestId] as const,
};

export function useCollectorSummary() {
  return useQuery({
    queryKey: collectorQueryKeys.summary,
    queryFn: getCollectorSummary,
  });
}

export function useAvailableCollectorRequests() {
  return useQuery({
    queryKey: collectorQueryKeys.available,
    queryFn: listAvailableCollectorRequests,
  });
}

export function useAssignedCollectorRequests() {
  return useQuery({
    queryKey: collectorQueryKeys.assigned,
    queryFn: listAssignedCollectorRequests,
  });
}

export function useCollectorPickupDetail(requestId: number | string) {
  return useQuery({
    queryKey: collectorQueryKeys.detail(requestId),
    queryFn: () => getCollectorPickupDetail(requestId),
    enabled: Boolean(requestId),
  });
}

interface CollectorMutationContext {
  previousAvailable?: PickupRequest[];
  previousAssigned?: PickupRequest[];
  previousDetail?: PickupRequestDetail;
}

function patchRequest<T extends PickupRequest | PickupRequestDetail>(
  request: T,
  patch: Partial<T>,
): T {
  return { ...request, ...patch };
}

function restoreOnError(
  queryClient: ReturnType<typeof useQueryClient>,
  requestId: number,
  context: CollectorMutationContext | undefined,
) {
  if (!context) {
    return;
  }

  if (context.previousAvailable) {
    queryClient.setQueryData(collectorQueryKeys.available, context.previousAvailable);
  }
  if (context.previousAssigned) {
    queryClient.setQueryData(collectorQueryKeys.assigned, context.previousAssigned);
  }
  if (context.previousDetail) {
    queryClient.setQueryData(collectorQueryKeys.detail(requestId), context.previousDetail);
  }
}

function invalidatePickupQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  requestId: number,
) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: collectorQueryKeys.available }),
    queryClient.invalidateQueries({ queryKey: collectorQueryKeys.assigned }),
    queryClient.invalidateQueries({ queryKey: collectorQueryKeys.summary }),
    queryClient.invalidateQueries({ queryKey: collectorQueryKeys.detail(requestId) }),
  ]);
}

async function cancelInFlightQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  requestId: number,
) {
  await Promise.all([
    queryClient.cancelQueries({ queryKey: collectorQueryKeys.available }),
    queryClient.cancelQueries({ queryKey: collectorQueryKeys.assigned }),
    queryClient.cancelQueries({ queryKey: collectorQueryKeys.detail(requestId) }),
  ]);
}

function useCollectorTransition(
  mutationFn: (requestId: number) => Promise<PickupRequest>,
  optimisticPatch: <T extends PickupRequest | PickupRequestDetail>(request: T) => T,
) {
  const queryClient = useQueryClient();

  return useMutation<PickupRequest, Error, number, CollectorMutationContext>({
    mutationFn,
    onMutate: async (requestId) => {
      await cancelInFlightQueries(queryClient, requestId);

      const previousAvailable = queryClient.getQueryData<PickupRequest[]>(
        collectorQueryKeys.available,
      );
      const previousAssigned = queryClient.getQueryData<PickupRequest[]>(
        collectorQueryKeys.assigned,
      );
      const previousDetail = queryClient.getQueryData<PickupRequestDetail>(
        collectorQueryKeys.detail(requestId),
      );

      if (previousAvailable) {
        queryClient.setQueryData<PickupRequest[]>(
          collectorQueryKeys.available,
          previousAvailable.map((request) =>
            request.id === requestId ? optimisticPatch(request) : request,
          ),
        );
      }
      if (previousAssigned) {
        queryClient.setQueryData<PickupRequest[]>(
          collectorQueryKeys.assigned,
          previousAssigned.map((request) =>
            request.id === requestId ? optimisticPatch(request) : request,
          ),
        );
      }
      if (previousDetail) {
        queryClient.setQueryData<PickupRequestDetail>(
          collectorQueryKeys.detail(requestId),
          optimisticPatch(previousDetail),
        );
      }

      return { previousAvailable, previousAssigned, previousDetail };
    },
    onError: (_error, requestId, context) => restoreOnError(queryClient, requestId, context),
    onSettled: (_data, _error, requestId) => {
      void invalidatePickupQueries(queryClient, requestId);
    },
  });
}

export function useAcceptCollectorPickup() {
  return useCollectorTransition(acceptCollectorPickup, (request) =>
    patchRequest(request, {
      status: "accepted",
      can_cancel: false,
      assignment: request.assignment ?? {
        id: 0,
        collector_id: 0,
        collector_name: request.assigned_collector_name ?? "",
        accepted_at: new Date().toISOString(),
        completed_at: null,
        weight_kg: null,
      },
    }),
  );
}

export function useStartCollectorPickup() {
  return useCollectorTransition(startCollectorPickup, (request) =>
    patchRequest(request, { status: "on_the_way" }),
  );
}

export function useCollectCollectorPickup() {
  return useCollectorTransition(collectCollectorPickup, (request) =>
    patchRequest(request, { status: "collected" }),
  );
}

export function useCompleteCollectorPickup() {
  const queryClient = useQueryClient();

  return useMutation<
    PickupRequest,
    Error,
    { requestId: number; weightKg: number },
    CollectorMutationContext
  >({
    mutationFn: ({ requestId, weightKg }) => completeCollectorPickup(requestId, weightKg),
    onMutate: async ({ requestId }) => {
      await cancelInFlightQueries(queryClient, requestId);

      const previousAvailable = queryClient.getQueryData<PickupRequest[]>(
        collectorQueryKeys.available,
      );
      const previousAssigned = queryClient.getQueryData<PickupRequest[]>(
        collectorQueryKeys.assigned,
      );
      const previousDetail = queryClient.getQueryData<PickupRequestDetail>(
        collectorQueryKeys.detail(requestId),
      );

      const markCompleted = (request: PickupRequest): PickupRequest =>
        patchRequest(request, {
          status: "completed",
          assignment: request.assignment
            ? { ...request.assignment, completed_at: new Date().toISOString() }
            : request.assignment,
        });

      if (previousAvailable) {
        queryClient.setQueryData<PickupRequest[]>(
          collectorQueryKeys.available,
          previousAvailable.map((request) =>
            request.id === requestId ? markCompleted(request) : request,
          ),
        );
      }
      if (previousAssigned) {
        queryClient.setQueryData<PickupRequest[]>(
          collectorQueryKeys.assigned,
          previousAssigned.map((request) =>
            request.id === requestId ? markCompleted(request) : request,
          ),
        );
      }
      if (previousDetail) {
        queryClient.setQueryData<PickupRequestDetail>(
          collectorQueryKeys.detail(requestId),
          markCompleted(previousDetail),
        );
      }

      return { previousAvailable, previousAssigned, previousDetail };
    },
    onError: (_error, variables, context) =>
      restoreOnError(queryClient, variables.requestId, context),
    onSettled: (_data, _error, variables) => {
      void invalidatePickupQueries(queryClient, variables.requestId);
    },
  });
}

export function useCancelCollectorPickup() {
  const queryClient = useQueryClient();

  return useMutation<PickupRequest, Error, number, CollectorMutationContext>({
    mutationFn: cancelCollectorPickup,
    onMutate: async (requestId) => {
      await cancelInFlightQueries(queryClient, requestId);

      const previousAvailable = queryClient.getQueryData<PickupRequest[]>(
        collectorQueryKeys.available,
      );
      const previousAssigned = queryClient.getQueryData<PickupRequest[]>(
        collectorQueryKeys.assigned,
      );
      const previousDetail = queryClient.getQueryData<PickupRequestDetail>(
        collectorQueryKeys.detail(requestId),
      );

      const releasedRequest = (request: PickupRequest): PickupRequest =>
        patchRequest(request, {
          status: "pending",
          can_cancel: true,
          assigned_collector_name: null,
          assignment: null,
        });

      if (previousAssigned) {
        const updated = previousAssigned.map((request) =>
          request.id === requestId ? releasedRequest(request) : request,
        );
        queryClient.setQueryData<PickupRequest[]>(collectorQueryKeys.assigned, updated);

        const released = previousAssigned.find((request) => request.id === requestId);
        if (released) {
          const previousAvailableRequests =
            queryClient.getQueryData<PickupRequest[]>(collectorQueryKeys.available) ??
            previousAvailable;
          const nextAvailable = [
            releasedRequest(released),
            ...(previousAvailableRequests?.filter((request) => request.id !== requestId) ?? []),
          ];
          queryClient.setQueryData<PickupRequest[]>(collectorQueryKeys.available, nextAvailable);
        }
      }
      if (previousDetail) {
        queryClient.setQueryData<PickupRequestDetail>(
          collectorQueryKeys.detail(requestId),
          releasedRequest(previousDetail),
        );
      }

      return { previousAvailable, previousAssigned, previousDetail };
    },
    onError: (_error, requestId, context) => restoreOnError(queryClient, requestId, context),
    onSettled: (_data, _error, requestId) => {
      void invalidatePickupQueries(queryClient, requestId);
    },
  });
}
