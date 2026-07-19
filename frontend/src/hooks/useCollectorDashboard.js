import { useQuery } from "@tanstack/react-query";

import { getCollectorSummary } from "../api/collector";

export const collectorQueryKeys = {
  summary: ["collector-summary"],
  availablePickups: ["available-pickups"],
  nearbyPickups: (latitude, longitude, radiusKm) => ["nearby-pickups", latitude, longitude, radiusKm],
  assignedPickups: ["assigned-pickups"]
};

export function useCollectorDashboard() {
  return useQuery({
    queryKey: collectorQueryKeys.summary,
    queryFn: getCollectorSummary
  });
}
