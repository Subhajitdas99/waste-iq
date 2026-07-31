import { BellRing, CheckCheck, Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";
import { NotificationCard } from "@/components/dashboard/NotificationCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { formatDateTime } from "@/lib/pickup";
import type { CitizenNotification } from "@/hooks/useCitizenNotifications";

interface NotificationsPanelProps {
  notifications: CitizenNotification[];
  unreadCount: number;
  isLoading?: boolean;
  onMarkAsRead: (id: string) => void;
  onMarkAllRead: () => void;
}

export function NotificationsPanel({
  notifications,
  unreadCount,
  isLoading = false,
  onMarkAsRead,
  onMarkAllRead,
}: NotificationsPanelProps) {
  return (
    <div className="space-y-4" aria-live="polite" aria-label="Notifications">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="rounded-2xl bg-primary/10 p-2.5 text-primary">
            <BellRing className="h-4 w-4" />
          </span>
          <p className="font-medium">
            Notifications
            {unreadCount > 0 ? (
              <span
                className="ml-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-xs font-semibold text-primary-foreground"
                aria-label={`${unreadCount} unread notifications`}
              >
                {unreadCount}
              </span>
            ) : null}
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="gap-2"
          onClick={onMarkAllRead}
          disabled={unreadCount === 0 || isLoading}
        >
          <CheckCheck className="h-4 w-4" />
          Mark all read
        </Button>
      </div>

      {isLoading ? (
        <LoadingSkeleton count={2} />
      ) : notifications.length > 0 ? (
        <ul className="space-y-4" role="list">
          {notifications.slice(0, 8).map((notification) => (
            <li key={notification.id}>
              {notification.read ? (
                <NotificationCard
                  title={notification.title}
                  message={notification.message}
                  timestamp={formatDateTime(notification.createdAt)}
                  className="opacity-80"
                />
              ) : (
                <button
                  type="button"
                  className="block w-full text-left"
                  onClick={() => onMarkAsRead(notification.id)}
                  aria-label={`Mark "${notification.title}" as read`}
                >
                  <NotificationCard
                    title={notification.title}
                    message={notification.message}
                    timestamp={formatDateTime(notification.createdAt)}
                    unread
                  />
                </button>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed bg-muted/20 px-4 py-8 text-center">
          <Inbox className="h-8 w-8 text-muted-foreground" />
          <p className="mt-3 font-medium">No notifications yet</p>
          <p className="mt-1 max-w-xs text-sm text-muted-foreground">
            You will be notified when a collector accepts, picks up, or completes your request.
          </p>
        </div>
      )}
    </div>
  );
}
