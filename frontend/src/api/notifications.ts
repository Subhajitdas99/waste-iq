import apiClient from "@/api/client";
import type {
  AppNotification,
  NotificationBroadcastPayload,
  NotificationBroadcastResult,
  NotificationBulkActionResult,
  NotificationListParams,
  NotificationPage,
  NotificationUnreadCount,
} from "@/types/notification";

export async function listNotifications(
  params: NotificationListParams = {},
): Promise<NotificationPage> {
  const response = await apiClient.get<NotificationPage>("/notifications", { params });
  return response.data;
}

export async function listUnreadNotifications(): Promise<AppNotification[]> {
  const response = await apiClient.get<AppNotification[]>("/notifications/unread");
  return response.data;
}

export async function getUnreadCount(): Promise<NotificationUnreadCount> {
  const response = await apiClient.get<NotificationUnreadCount>("/notifications/unread/count");
  return response.data;
}

export async function getNotification(id: number): Promise<AppNotification> {
  const response = await apiClient.get<AppNotification>(`/notifications/${id}`);
  return response.data;
}

export async function markRead(id: number): Promise<AppNotification> {
  const response = await apiClient.post<AppNotification>(`/notifications/${id}/read`);
  return response.data;
}

export async function markAllRead(): Promise<NotificationBulkActionResult> {
  const response = await apiClient.post<NotificationBulkActionResult>("/notifications/read-all");
  return response.data;
}

export async function deleteNotification(id: number): Promise<void> {
  await apiClient.delete(`/notifications/${id}`);
}

export async function deleteRead(): Promise<NotificationBulkActionResult> {
  const response = await apiClient.delete<NotificationBulkActionResult>("/notifications/read");
  return response.data;
}

export async function broadcastNotification(
  payload: NotificationBroadcastPayload,
): Promise<NotificationBroadcastResult> {
  const response = await apiClient.post<NotificationBroadcastResult>(
    "/admin/notifications/broadcast",
    payload,
  );
  return response.data;
}