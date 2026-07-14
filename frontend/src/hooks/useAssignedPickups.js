import { useQuery } from "@tanstack/react-query";

import { getAssignedPickups } from "../api/collector";
import { collectorQueryKeys } from "./useCollectorDashboard";

export function useAssignedPickups() {
  return useQuery({
    queryKey: collectorQueryKeys.assignedPickups,
    queryFn: getAssignedPickups
  });
}
