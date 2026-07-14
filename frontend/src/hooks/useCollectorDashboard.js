import { useQuery } from "@tanstack/react-query";

import { getCollectorSummary } from "../api/collector";

export const collectorQueryKeys = {
  summary: ["collector-summary"],
  availablePickups: ["available-pickups"],
  assignedPickups: ["assigned-pickups"]
};

export function useCollectorDashboard() {
  return useQuery({
    queryKey: collectorQueryKeys.summary,
    queryFn: getCollectorSummary
  });
}
