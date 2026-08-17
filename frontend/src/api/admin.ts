import apiClient from "@/api/client";
import type {
  AdminAnalytics,
  AdminDealerDetail,
  AdminDealerListPage,
  AdminDealerListQuery,
  AdminUser,
} from "@/types/admin";
import type { DealerApprovalAction } from "@/types/dealer";

export async function getAdminAnalytics(): Promise<AdminAnalytics> {
  const response = await apiClient.get<AdminAnalytics>("/admin/analytics");
  return response.data;
}

export async function listAdminUsers(): Promise<AdminUser[]> {
  const response = await apiClient.get<AdminUser[]>("/admin/users");
  return response.data;
}

export async function listAdminDealers(
  query: AdminDealerListQuery = {},
): Promise<AdminDealerListPage> {
  const response = await apiClient.get<AdminDealerListPage>("/admin/dealers", {
    params: query,
  });
  return response.data;
}

export async function listPendingAdminDealers(
  query: AdminDealerListQuery = {},
): Promise<AdminDealerListPage> {
  const response = await apiClient.get<AdminDealerListPage>(
    "/admin/dealers/pending",
    { params: query },
  );
  return response.data;
}

export async function getAdminDealerDetail(
  dealerUserId: number,
): Promise<AdminDealerDetail> {
  const response = await apiClient.get<AdminDealerDetail>(
    `/admin/dealers/${dealerUserId}`,
  );
  return response.data;
}

export async function approveAdminDealer(
  dealerUserId: number,
): Promise<DealerApprovalAction> {
  const response = await apiClient.post<DealerApprovalAction>(
    `/admin/dealers/${dealerUserId}/approve`,
  );
  return response.data;
}

export async function rejectAdminDealer(
  dealerUserId: number,
  reason: string,
): Promise<DealerApprovalAction> {
  const response = await apiClient.post<DealerApprovalAction>(
    `/admin/dealers/${dealerUserId}/reject`,
    { reason },
  );
  return response.data;
}
