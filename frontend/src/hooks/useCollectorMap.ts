import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getCollectorLocation,
  getCollectorMap,
  getCollectorNavigation,
  getCollectorRoute,
  listNearbyPickups,
  updateCollectorLocation,
} from "@/api/collectorMap";
import type {
  CollectorLocation,
  CollectorLocationUpdatePayload,
  CollectorMapPayload,
  Navigation,
} from "@/types/map";

export const collectorMapQueryKeys = {
  all: ["collector", "map"] as const,
  map: (radiusKm = 5) => ["collector", "map", "map", radiusKm] as const,
  location: ["collector", "map", "location"] as const,
  route: ["collector", "map", "route"] as const,
  nearby: ["collector", "map", "nearby"] as const,
  navigation: (pickupId: number) => ["collector", "map", "navigation", pickupId] as const,
};

export function useCollectorMap(radiusKm = 5) {
  return useQuery({
    queryKey: collectorMapQueryKeys.map(radiusKm),
    queryFn: () => getCollectorMap({ radiusKm }),
  });
}

export function useCollectorLocation() {
  return useQuery({
    queryKey: collectorMapQueryKeys.location,
    queryFn: getCollectorLocation,
  });
}

export function useCollectorRoute() {
  return useQuery({
    queryKey: collectorMapQueryKeys.route,
    queryFn: () => getCollectorRoute(),
  });
}

export function useNearbyPickups(radiusKm = 5) {
  return useQuery({
    queryKey: collectorMapQueryKeys.nearby,
    queryFn: () => listNearbyPickups({ radiusKm }),
  });
}

export function useCollectorNavigation(pickupId: number | null) {
  return useQuery<Navigation>({
    queryKey: collectorMapQueryKeys.navigation(pickupId ?? 0),
    queryFn: () => getCollectorNavigation(pickupId as number),
    enabled: pickupId !== null,
  });
}

interface LocationUpdateContext {
  previousLocations: Array<readonly [readonly unknown[], CollectorLocation | undefined]>;
  previousMaps: Array<readonly [readonly unknown[], CollectorMapPayload | undefined]>;
}

export function useUpdateCollectorLocation() {
  const queryClient = useQueryClient();

  return useMutation<CollectorLocation, Error, CollectorLocationUpdatePayload, LocationUpdateContext>({
    mutationFn: updateCollectorLocation,
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: collectorMapQueryKeys.all });

      const optimisticLocation: CollectorLocation = {
        latitude: payload.latitude,
        longitude: payload.longitude,
        accuracy: payload.accuracy ?? null,
        updated_at: new Date().toISOString(),
      };

      const previousLocations = queryClient.getQueriesData<CollectorLocation>({
        queryKey: collectorMapQueryKeys.location,
      });
      queryClient.setQueryData<CollectorLocation>(
        collectorMapQueryKeys.location,
        optimisticLocation,
      );

      const previousMaps = queryClient.getQueriesData<CollectorMapPayload>({
        queryKey: collectorMapQueryKeys.map(),
      });
      for (const [key, mapData] of previousMaps) {
        if (mapData) {
          queryClient.setQueryData<CollectorMapPayload>(key, {
            ...mapData,
            collector: optimisticLocation,
          });
        }
      }

      return { previousLocations, previousMaps };
    },
    onError: (_error, _payload, context) => {
      if (!context) {
        return;
      }
      for (const [key, data] of context.previousLocations) {
        queryClient.setQueryData<CollectorLocation>(key, data);
      }
      for (const [key, data] of context.previousMaps) {
        queryClient.setQueryData<CollectorMapPayload>(key, data);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: collectorMapQueryKeys.all });
    },
  });
}