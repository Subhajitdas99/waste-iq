export type NotificationType =
  | "pickup_created"
  | "pickup_accepted"
  | "pickup_started"
  | "pickup_collected"
  | "pickup_completed"
  | "weight_recorded"
  | "weight_confirmed"
  | "weight_disputed"
  | "dispute_resolved"
  | "dealer_profile_submitted"
  | "dealer_profile_approved"
  | "dealer_profile_rejected"
  | "inventory_created"
  | "inventory_reserved"
  | "reservation_cancelled"
  | "reservation_expired"
  | "inventory_purchased"
  | "admin_announcement"
  | "system";

export type NotificationStatus = "unread" | "read";

export type NotificationRole = "citizen" | "collector" | "dealer" | "admin";

export interface AppNotification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: NotificationType;
  status: NotificationStatus;
  link: string | null;
  metadata_json: Record<string, unknown> | null;
  read_at: string | null;
  created_at: string;
}

export interface NotificationPage {
  items: AppNotification[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface NotificationListParams {
  page?: number;
  page_size?: number;
  status?: NotificationStatus;
}

export interface NotificationUnreadCount {
  unread_count: number;
}

export interface NotificationBulkActionResult {
  affected: number;
}

export interface NotificationBroadcastPayload {
  title: string;
  message: string;
  link?: string | null;
  type?: NotificationType;
  recipient_roles?: NotificationRole[];
}

export interface NotificationBroadcastResult {
  type: NotificationType;
  title: string;
  message: string;
  link: string | null;
  recipients_count: number;
}