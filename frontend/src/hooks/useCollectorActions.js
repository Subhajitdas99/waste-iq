import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  acceptPickup,
  collectPickup,
  completePickup,
  startPickup
} from "../api/collector";
import { collectorQueryKeys } from "./useCollectorDashboard";
import { pickupRequestQueryKeys } from "./usePickupRequests";

function invalidateCollectorQueries(queryClient) {
  queryClient.invalidateQueries({ queryKey: collectorQueryKeys.summary });
  queryClient.invalidateQueries({ queryKey: collectorQueryKeys.availablePickups });
  queryClient.invalidateQueries({ queryKey: collectorQueryKeys.assignedPickups });
  queryClient.invalidateQueries({ queryKey: pickupRequestQueryKeys.all });
}

export function useCollectorActions() {
  const queryClient = useQueryClient();

  const mutationOptions = {
    onSuccess: () => {
      invalidateCollectorQueries(queryClient);
    }
  };

  return {
    accept: useMutation({
      mutationFn: acceptPickup,
      ...mutationOptions
    }),
    start: useMutation({
      mutationFn: startPickup,
      ...mutationOptions
    }),
    collect: useMutation({
      mutationFn: collectPickup,
      ...mutationOptions
    }),
    complete: useMutation({
      mutationFn: ({ id, weight }) => completePickup(id, weight),
      ...mutationOptions
    })
  };
}
