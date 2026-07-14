import { useQuery } from "@tanstack/react-query";

import { getAvailablePickups } from "../api/collector";
import { collectorQueryKeys } from "./useCollectorDashboard";

export function useAvailablePickups() {
  return useQuery({
    queryKey: collectorQueryKeys.availablePickups,
    queryFn: getAvailablePickups
  });
}
