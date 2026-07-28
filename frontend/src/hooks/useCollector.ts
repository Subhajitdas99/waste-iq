import { useQuery } from "@tanstack/react-query";
import { getCollectorSummary } from "@/api/collector";

export function useCollectorSummary() {
  return useQuery({
    queryKey: ["collector-summary"],
    queryFn: getCollectorSummary,
    staleTime: 30000,
  });
}
