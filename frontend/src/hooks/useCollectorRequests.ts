import { useQuery } from "@tanstack/react-query";
import {
  getCollectorSummary,
  listAvailableCollectorRequests,
} from "@/api/collector";

export const collectorQueryKeys = {
  all: ["collector"] as const,
  summary: ["collector", "summary"] as const,
  available: ["collector", "available"] as const,
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
