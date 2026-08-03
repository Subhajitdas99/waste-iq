import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  cancelMarketplaceReservation,
  getMarketplaceInventory,
  getMarketplaceOrder,
  listMarketplaceInventory,
  listMarketplaceOrders,
  listMarketplaceTransactions,
  purchaseMarketplaceInventory,
  reserveMarketplaceInventory,
} from "@/api/marketplace";
import type {
  MarketplaceInventoryQuery,
  MarketplaceTransactionType,
} from "@/types/marketplace";

export const marketplaceKeys = {
  all: ["marketplace"] as const,
  inventoryLists: () => [...marketplaceKeys.all, "inventory", "list"] as const,
  inventoryList: (query: MarketplaceInventoryQuery) =>
    [...marketplaceKeys.inventoryLists(), query] as const,
  inventoryDetails: () => [...marketplaceKeys.all, "inventory", "detail"] as const,
  inventoryDetail: (id: number) => [...marketplaceKeys.inventoryDetails(), id] as const,
  ordersLists: () => [...marketplaceKeys.all, "orders", "list"] as const,
  ordersList: (page: number, pageSize: number) =>
    [...marketplaceKeys.ordersLists(), { page, pageSize }] as const,
  orderDetails: () => [...marketplaceKeys.all, "orders", "detail"] as const,
  orderDetail: (id: number) => [...marketplaceKeys.orderDetails(), id] as const,
  transactionLists: () => [...marketplaceKeys.all, "transactions", "list"] as const,
  transactionList: (page: number, pageSize: number, type?: MarketplaceTransactionType) =>
    [...marketplaceKeys.transactionLists(), { page, pageSize, type }] as const,
};

export function useMarketplaceInventory(query: MarketplaceInventoryQuery) {
  return useQuery({
    queryKey: marketplaceKeys.inventoryList(query),
    queryFn: () => listMarketplaceInventory(query),
  });
}

export function useMarketplaceItem(id: number) {
  return useQuery({
    queryKey: marketplaceKeys.inventoryDetail(id),
    queryFn: () => getMarketplaceInventory(id),
    enabled: !!id,
  });
}

export function useMarketplaceOrders(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: marketplaceKeys.ordersList(page, pageSize),
    queryFn: () => listMarketplaceOrders(page, pageSize),
  });
}

export function useMarketplaceOrderDetail(id: number) {
  return useQuery({
    queryKey: marketplaceKeys.orderDetail(id),
    queryFn: () => getMarketplaceOrder(id),
    enabled: !!id,
  });
}

export function useMarketplaceTransactions(
  page = 1,
  pageSize = 20,
  type?: MarketplaceTransactionType,
) {
  return useQuery({
    queryKey: marketplaceKeys.transactionList(page, pageSize, type),
    queryFn: () => listMarketplaceTransactions(page, pageSize, type),
  });
}

export function useReserveInventory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => reserveMarketplaceInventory(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.inventoryLists() });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.inventoryDetail(id) });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.transactionLists() });
    },
  });
}

export function useCancelReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => cancelMarketplaceReservation(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.inventoryLists() });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.inventoryDetail(id) });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.transactionLists() });
    },
  });
}

export function usePurchaseInventory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => purchaseMarketplaceInventory(id),
    onSuccess: (order, id) => {
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.inventoryLists() });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.inventoryDetail(id) });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.ordersLists() });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.orderDetail(order.id) });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.transactionLists() });
    },
  });
}
