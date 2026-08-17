import { Skeleton } from "@/components/ui/skeleton";
import type { AppNotification } from "@/types/notification";
import { EmptyNotifications } from "./EmptyNotifications";
import { NotificationCard } from "./NotificationCard";

interface NotificationListProps {
  notifications: AppNotification[];
  isLoading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  onMarkRead?: (id: number) => void;
  onDelete?: (id: number) => void;
}

export function NotificationList({
  notifications,
  isLoading,
  emptyTitle = "No notifications yet",
  emptyDescription = "Updates about pickups, inventory, and account activity will appear here.",
  onMarkRead,
  onDelete,
}: NotificationListProps) {
  if (isLoading) {
    return (
      <div className="space-y-0">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="flex items-start gap-3 border-b border-white/10 p-4">
            <Skeleton className="h-9 w-9 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-3 w-3/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (notifications.length === 0) {
    return <EmptyNotifications title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="divide-y divide-white/10">
      {notifications.map((notification) => (
        <NotificationCard
          key={notification.id}
          notification={notification}
          onMarkRead={onMarkRead}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}