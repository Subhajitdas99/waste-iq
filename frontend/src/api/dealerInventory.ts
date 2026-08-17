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

import type {
  DealerInventory,
  DealerInventoryBase,
  DealerInventoryPage,
  DealerInventoryUpdate,
} from "@/types/dealerInventory";

export const dealerStockApi = {
  list: async (page = 1, pageSize = 20, status?: string): Promise<DealerInventoryPage> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (status) {
      params.append("status", status);
    }
    const response = await apiClient.get(`/dealer/inventory?${params.toString()}`);
    return response.data;
  },

  get: async (id: number): Promise<DealerInventory> => {
    const response = await apiClient.get(`/dealer/inventory/${id}`);
    return response.data;
  },

  create: async (data: DealerInventoryBase): Promise<DealerInventory> => {
    const response = await apiClient.post("/dealer/inventory", data);
    return response.data;
  },

  update: async (id: number, data: DealerInventoryUpdate): Promise<DealerInventory> => {
    const response = await apiClient.put(`/dealer/inventory/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/dealer/inventory/${id}`);
  },

  reserve: async (id: number): Promise<DealerInventory> => {
    const response = await apiClient.post(`/dealer/inventory/${id}/reserve`);
    return response.data;
  },

  release: async (id: number): Promise<DealerInventory> => {
    const response = await apiClient.post(`/dealer/inventory/${id}/release`);
    return response.data;
  },

  markSold: async (id: number): Promise<DealerInventory> => {
    const response = await apiClient.post(`/dealer/inventory/${id}/mark-sold`);
    return response.data;
  },
};
