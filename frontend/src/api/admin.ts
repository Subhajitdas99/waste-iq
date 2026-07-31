import apiClient from "@/api/client";
import type {
  AdminAnalytics,
  AdminDealerSummary,
  AdminUser,
} from "@/types/admin";

export async function getAdminAnalytics(): Promise<AdminAnalytics> {
  const response = await apiClient.get<AdminAnalytics>("/admin/analytics");
  return response.data;
}

export async function listAdminUsers(): Promise<AdminUser[]> {
  const response = await apiClient.get<AdminUser[]>("/admin/users");
  return response.data;
}

export async function listAdminDealers(): Promise<AdminDealerSummary[]> {
  const response = await apiClient.get<AdminDealerSummary[]>("/admin/dealers");
  return response.data;
}
