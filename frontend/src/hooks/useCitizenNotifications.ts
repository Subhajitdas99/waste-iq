import { useEffect, useState } from "react";
import type { PickupRequest, PickupStatus } from "@/types/pickup";

export type NotificationStatus = PickupStatus | "created";

export interface CitizenNotification {
  id: string;
  requestId: number;
  status: NotificationStatus;
  title: string;
  message: string;
  createdAt: string;
  read: boolean;
}

export type PickupStatusMap = Record<string, PickupStatus>;

const NOTIFICATIONS_STORAGE_KEY = "wasteiq_citizen_notifications_v1";
const STATUS_MAP_STORAGE_KEY = "wasteiq_citizen_pickup_statuses_v1";
const MAX_NOTIFICATIONS = 30;

function readStorage<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeStorage<T>(key: string, value: T): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage unavailable or full — notifications degrade silently.
  }
}

export function buildNotificationTitle(status: NotificationStatus): string {
  switch (status) {
    case "created":
      return "Pickup request submitted";
    case "accepted":
      return "Pickup accepted";
    case "on_the_way":
      return "Collector on the way";
    case "collected":
      return "Waste collected";
    case "completed":
      return "Pickup completed";
    case "cancelled":
      return "Pickup cancelled";
    default:
      return "Pickup updated";
  }
}

export function buildNotificationMessage(
  request: PickupRequest,
  status: NotificationStatus,
): string {
  switch (status) {
    case "created":
      return `Request #${request.id} is queued and waiting for a collector.`;
    case "accepted":
      return request.assigned_collector_name
        ? `${request.assigned_collector_name} accepted request #${request.id}.`
        : `A collector accepted request #${request.id}.`;
    case "on_the_way":
      return request.assigned_collector_name
        ? `${request.assigned_collector_name} is on the way to request #${request.id}.`
        : `The collector is on the way to request #${request.id}.`;
    case "collected":
      return `Waste for request #${request.id} has been collected and is awaiting confirmation.`;
    case "completed":
      return request.assignment?.weight_kg != null
        ? `Request #${request.id} completed with ${request.assignment.weight_kg.toFixed(1)} kg reported.`
        : `Request #${request.id} was completed.`;
    case "cancelled":
      return `Request #${request.id} was cancelled.`;
    default:
      return `Request #${request.id} was updated.`;
  }
}

export function deriveNotifications(
  requests: PickupRequest[],
  previousStatusMap: PickupStatusMap,
  existingNotifications: CitizenNotification[],
): { notifications: CitizenNotification[]; nextStatusMap: PickupStatusMap } {
  const isFirstRun =
    Object.keys(previousStatusMap).length === 0 && existingNotifications.length === 0;

  const nextStatusMap: PickupStatusMap = { ...previousStatusMap };
  let statusMapChanged = false;
  const seenIds = new Set(existingNotifications.map((notification) => notification.id));
  const additions: CitizenNotification[] = [];
  const now = new Date().toISOString();

  for (const request of requests) {
    const key = String(request.id);
    const previousStatus = previousStatusMap[key];
    const nextStatus: NotificationStatus = previousStatus === undefined ? "created" : request.status;

    if (previousStatus !== request.status) {
      statusMapChanged = true;
      nextStatusMap[key] = request.status;
    }

    if (!isFirstRun && previousStatus !== request.status) {
      const notificationId = `${request.id}:${nextStatus}`;
      if (!seenIds.has(notificationId)) {
        additions.push({
          id: notificationId,
          requestId: request.id,
          status: nextStatus,
          title: buildNotificationTitle(nextStatus),
          message: buildNotificationMessage(request, nextStatus),
          createdAt: now,
          read: false,
        });
      }
    }
  }

  if (isFirstRun) {
    return { notifications: existingNotifications, nextStatusMap };
  }

  if (!statusMapChanged && additions.length === 0) {
    return { notifications: existingNotifications, nextStatusMap: previousStatusMap };
  }

  return {
    notifications: [...additions, ...existingNotifications].slice(0, MAX_NOTIFICATIONS),
    nextStatusMap,
  };
}

export function useCitizenNotifications(requests: PickupRequest[] | undefined) {
  const [notifications, setNotifications] = useState<CitizenNotification[]>(() =>
    readStorage<CitizenNotification[]>(NOTIFICATIONS_STORAGE_KEY, []),
  );
  const [statusMap, setStatusMap] = useState<PickupStatusMap>(() =>
    readStorage<PickupStatusMap>(STATUS_MAP_STORAGE_KEY, {}),
  );

  useEffect(() => {
    if (!requests) {
      return;
    }

    const result = deriveNotifications(requests, statusMap, notifications);
    setNotifications(result.notifications);
    setStatusMap(result.nextStatusMap);

    writeStorage(NOTIFICATIONS_STORAGE_KEY, result.notifications);
    writeStorage(STATUS_MAP_STORAGE_KEY, result.nextStatusMap);
  }, [requests, statusMap, notifications]);

  const unreadCount = notifications.filter((notification) => !notification.read).length;

  const markAsRead = (id: string) => {
    setNotifications((current) => {
      const next = current.map((notification) =>
        notification.id === id ? { ...notification, read: true } : notification,
      );
      writeStorage(NOTIFICATIONS_STORAGE_KEY, next);
      return next;
    });
  };

  const markAllRead = () => {
    setNotifications((current) => {
      if (current.every((notification) => notification.read)) {
        return current;
      }
      const next = current.map((notification) => ({ ...notification, read: true }));
      writeStorage(NOTIFICATIONS_STORAGE_KEY, next);
      return next;
    });
  };

  return { notifications, unreadCount, markAsRead, markAllRead };
}
