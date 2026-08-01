import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { dealerStockApi } from "@/api/dealerInventory";
import type { DealerInventoryBase, DealerInventoryUpdate } from "@/types/dealerInventory";

export const dealerStockKeys = {
  all: ["dealerStock"] as const,
  lists: () => [...dealerStockKeys.all, "list"] as const,
  list: (page: number, pageSize: number, status?: string) =>
    [...dealerStockKeys.lists(), { page, pageSize, status }] as const,
  details: () => [...dealerStockKeys.all, "detail"] as const,
  detail: (id: number) => [...dealerStockKeys.details(), id] as const,
};

export function useDealerStockList(page = 1, pageSize = 20, status?: string) {
  return useQuery({
    queryKey: dealerStockKeys.list(page, pageSize, status),
    queryFn: () => dealerStockApi.list(page, pageSize, status),
  });
}

export function useDealerStockDetail(id: number) {
  return useQuery({
    queryKey: dealerStockKeys.detail(id),
    queryFn: () => dealerStockApi.get(id),
    enabled: !!id,
  });
}

export function useCreateDealerStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DealerInventoryBase) => dealerStockApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.lists() });
    },
  });
}

export function useUpdateDealerStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: DealerInventoryUpdate }) =>
      dealerStockApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.lists() });
    },
  });
}

export function useDeleteDealerStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => dealerStockApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.lists() });
    },
  });
}

export function useReserveDealerStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => dealerStockApi.reserve(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.lists() });
    },
  });
}

export function useReleaseDealerStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => dealerStockApi.release(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.lists() });
    },
  });
}

export function useMarkDealerStockSold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => dealerStockApi.markSold(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: dealerStockKeys.lists() });
    },
  });
}
