import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteNotification,
  deleteRead,
  getNotification,
  getUnreadCount,
  listNotifications,
  listUnreadNotifications,
  markAllRead,
  markRead,
} from "@/api/notifications";
import type {
  AppNotification,
  NotificationStatus,
} from "@/types/notification";

export const notificationQueryKeys = {
  all: ["notifications"] as const,
  page: (page: number, pageSize: number, status?: NotificationStatus) =>
    ["notifications", "page", { page, pageSize, status }] as const,
  detail: (id: number) => ["notifications", "detail", id] as const,
  unread: ["notifications", "unread"] as const,
  unreadCount: ["notifications", "unreadCount"] as const,
};

export const NOTIFICATION_REFRESH_INTERVAL_MS = 30_000;

function withReadState(notification: AppNotification): AppNotification {
  return {
    ...notification,
    status: "read",
    read_at: new Date().toISOString(),
  };
}

export function useNotifications(
  page = 1,
  pageSize = 20,
  status?: NotificationStatus,
) {
  return useQuery({
    queryKey: notificationQueryKeys.page(page, pageSize, status),
    queryFn: () => listNotifications({ page, page_size: pageSize, status }),
    refetchInterval: NOTIFICATION_REFRESH_INTERVAL_MS,
  });
}

export function useUnreadNotifications() {
  return useQuery({
    queryKey: notificationQueryKeys.unread,
    queryFn: listUnreadNotifications,
    refetchInterval: NOTIFICATION_REFRESH_INTERVAL_MS,
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: notificationQueryKeys.unreadCount,
    queryFn: getUnreadCount,
    refetchInterval: NOTIFICATION_REFRESH_INTERVAL_MS,
  });
}

export function useNotification(id: number) {
  return useQuery({
    queryKey: notificationQueryKeys.detail(id),
    queryFn: () => getNotification(id),
  });
}

export function useMarkRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markRead,
    onMutate: async (id: number) => {
      await queryClient.cancelQueries({ queryKey: notificationQueryKeys.all });

      const previousUnread = queryClient.getQueryData<AppNotification[]>(
        notificationQueryKeys.unread,
      );

      queryClient.setQueryData<AppNotification[]>(
        notificationQueryKeys.unread,
        (current) =>
          current
            ?.filter((notification) => notification.id !== id)
            .map((notification) =>
              notification.id === id ? withReadState(notification) : notification,
            ),
      );

      queryClient.setQueriesData<{ items: AppNotification[] }>(
        { queryKey: ["notifications", "page"], type: "active" },
        (current) =>
          current
            ? {
                ...current,
                items: current.items.map((notification) =>
                  notification.id === id && notification.status === "unread"
                    ? withReadState(notification)
                    : notification,
                ),
              }
            : current,
      );

      queryClient.setQueryData<AppNotification | undefined>(
        notificationQueryKeys.detail(id),
        (current) =>
          current && current.status === "unread" ? withReadState(current) : current,
      );

      queryClient.setQueryData<{ unread_count: number }>(
        notificationQueryKeys.unreadCount,
        (current) =>
          current ? { unread_count: Math.max(0, current.unread_count - 1) } : current,
      );

      return { previousUnread };
    },
    onError: (_error, _id, context) => {
      queryClient.setQueryData(notificationQueryKeys.unread, context?.previousUnread);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: notificationQueryKeys.all });
    },
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markAllRead,
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: notificationQueryKeys.all });

      queryClient.setQueryData<AppNotification[]>(notificationQueryKeys.unread, () => []);
      queryClient.setQueryData<{ unread_count: number }>(
        notificationQueryKeys.unreadCount,
        () => ({ unread_count: 0 }),
      );
      queryClient.setQueriesData<{ items: AppNotification[] }>(
        { queryKey: ["notifications", "page"] },
        (current) =>
          current
            ? {
                ...current,
                items: current.items.map((notification) =>
                  notification.status === "unread"
                    ? withReadState(notification)
                    : notification,
                ),
              }
            : current,
      );
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: notificationQueryKeys.all });
    },
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteNotification,
    onMutate: async (id: number) => {
      await queryClient.cancelQueries({ queryKey: notificationQueryKeys.all });

      const previousUnread = queryClient.getQueryData<AppNotification[]>(
        notificationQueryKeys.unread,
      );

      queryClient.setQueryData<AppNotification[]>(
        notificationQueryKeys.unread,
        (current) => current?.filter((notification) => notification.id !== id) ?? [],
      );

      queryClient.setQueryData(
        notificationQueryKeys.detail(id),
        () => undefined,
      );

      return { previousUnread };
    },
    onError: (_error, _id, context) => {
      queryClient.setQueryData(notificationQueryKeys.unread, context?.previousUnread);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: notificationQueryKeys.all });
    },
  });
}

export function useDeleteRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteRead,
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: notificationQueryKeys.all });

      queryClient.setQueryData<AppNotification[]>(
        notificationQueryKeys.unread,
        (current) => current ?? [],
      );
      queryClient.setQueryData<{ unread_count: number }>(
        notificationQueryKeys.unreadCount,
        (current) => current ?? { unread_count: 0 },
      );
      queryClient.setQueriesData<{ items: AppNotification[] }>(
        { queryKey: ["notifications", "page"] },
        (current) =>
          current
            ? { ...current, items: current.items.filter((n) => n.status !== "read") }
            : current,
      );
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: notificationQueryKeys.all });
    },
  });
}