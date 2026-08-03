import apiClient from "@/api/client";
import type {
  MarketplaceInventoryLot,
  MarketplaceInventoryPage,
  MarketplaceInventoryQuery,
  MarketplaceOrder,
  MarketplaceOrderDetail,
  MarketplaceOrderPage,
  MarketplaceTransaction,
  MarketplaceTransactionPage,
  MarketplaceTransactionType,
} from "@/types/marketplace";

export async function listMarketplaceInventory(
  query: MarketplaceInventoryQuery = {},
): Promise<MarketplaceInventoryPage> {
  const response = await apiClient.get<MarketplaceInventoryPage>("/marketplace/inventory", {
    params: query,
  });
  return response.data;
}

export async function getMarketplaceInventory(id: number): Promise<MarketplaceInventoryLot> {
  const response = await apiClient.get<MarketplaceInventoryLot>(`/marketplace/inventory/${id}`);
  return response.data;
}

export async function reserveMarketplaceInventory(id: number): Promise<MarketplaceInventoryLot> {
  const response = await apiClient.post<MarketplaceInventoryLot>(
    `/marketplace/inventory/${id}/reserve`,
  );
  return response.data;
}

export async function cancelMarketplaceReservation(id: number): Promise<MarketplaceInventoryLot> {
  const response = await apiClient.post<MarketplaceInventoryLot>(
    `/marketplace/inventory/${id}/cancel-reservation`,
  );
  return response.data;
}

export async function purchaseMarketplaceInventory(id: number): Promise<MarketplaceOrderDetail> {
  const response = await apiClient.post<MarketplaceOrderDetail>(
    `/marketplace/inventory/${id}/purchase`,
  );
  return response.data;
}

export async function listMarketplaceOrders(
  page = 1,
  pageSize = 20,
): Promise<MarketplaceOrderPage> {
  const response = await apiClient.get<MarketplaceOrderPage>("/marketplace/orders", {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

export async function getMarketplaceOrder(id: number): Promise<MarketplaceOrderDetail> {
  const response = await apiClient.get<MarketplaceOrderDetail>(`/marketplace/orders/${id}`);
  return response.data;
}

export async function listMarketplaceTransactions(
  page = 1,
  pageSize = 20,
  transactionType?: MarketplaceTransactionType,
): Promise<MarketplaceTransactionPage> {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (transactionType) {
    params.transaction_type = transactionType;
  }
  const response = await apiClient.get<MarketplaceTransactionPage>("/marketplace/transactions", {
    params,
  });
  return response.data;
}

export type {
  MarketplaceInventoryLot,
  MarketplaceInventoryPage,
  MarketplaceOrder,
  MarketplaceOrderDetail,
  MarketplaceTransaction,
};
