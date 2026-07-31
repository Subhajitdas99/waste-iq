import apiClient from "@/api/client";
import type {
  DealerInventoryLotPage,
  DealerInventoryQuery,
} from "@/types/inventory";

export async function listDealerInventoryLots(
  query: DealerInventoryQuery = {},
): Promise<DealerInventoryLotPage> {
  const response = await apiClient.get<DealerInventoryLotPage>(
    "/dealer/inventory-lots",
    { params: query },
  );

  return response.data;
}
