import { useQuery } from "@tanstack/react-query";
import { listDealerInventoryLots } from "@/api/dealerInventory";
import type { DealerInventoryQuery } from "@/types/inventory";

export const dealerInventoryQueryKeys = {
  all: ["dealer", "inventory"] as const,
  list: (query: DealerInventoryQuery) => ["dealer", "inventory", query] as const,
};

export function useDealerInventory(query: DealerInventoryQuery) {
  return useQuery({
    queryKey: dealerInventoryQueryKeys.list(query),
    queryFn: () => listDealerInventoryLots(query),
  });
}
