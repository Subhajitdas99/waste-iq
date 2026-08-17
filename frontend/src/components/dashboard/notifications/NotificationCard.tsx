import type { ComponentType } from "react";
import { Link } from "react-router-dom";
import {
  BellRing,
  CalendarClock,
  Megaphone,
  Package,
  Store,
  Trash2,
  Truck,
  UserCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatNotificationTimestamp } from "@/lib/notification";
import { cn } from "@/lib/utils";
import type { AppNotification, NotificationType } from "@/types/notification";

interface TypeStyle {
  icon: ComponentType<{ className?: string }>;
  iconClassName: string;
}

const NOTIFICATION_TYPE_STYLES: Record<NotificationType, TypeStyle> = {
  pickup_created: { icon: Truck, iconClassName: "bg-emerald-100 text-emerald-700" },
  pickup_accepted: { icon: Truck, iconClassName: "bg-emerald-100 text-emerald-700" },
  pickup_started: { icon: Truck, iconClassName: "bg-emerald-100 text-emerald-700" },
  pickup_collected: { icon: Truck, iconClassName: "bg-emerald-100 text-emerald-700" },
  pickup_completed: { icon: Truck, iconClassName: "bg-emerald-100 text-emerald-700" },
  dealer_profile_submitted: { icon: UserCheck, iconClassName: "bg-sky-100 text-sky-700" },
  dealer_profile_approved: { icon: UserCheck, iconClassName: "bg-sky-100 text-sky-700" },
  dealer_profile_rejected: { icon: UserCheck, iconClassName: "bg-sky-100 text-sky-700" },
  inventory_created: { icon: Package, iconClassName: "bg-amber-100 text-amber-700" },
  inventory_reserved: { icon: Package, iconClassName: "bg-amber-100 text-amber-700" },
  reservation_cancelled: { icon: CalendarClock, iconClassName: "bg-amber-100 text-amber-700" },
  reservation_expired: { icon: CalendarClock, iconClassName: "bg-amber-100 text-amber-700" },
  inventory_purchased: { icon: Store, iconClassName: "bg-violet-100 text-violet-700" },
  admin_announcement: { icon: Megaphone, iconClassName: "bg-rose-100 text-rose-700" },
  system: { icon: BellRing, iconClassName: "bg-slate-100 text-slate-700" },
};

interface NotificationCardProps {
  notification: AppNotification;
  onMarkRead?: (id: number) => void;
  onDelete?: (id: number) => void;
}

export function NotificationCard({ notification, onMarkRead, onDelete }: NotificationCardProps) {
  const typeStyle = NOTIFICATION_TYPE_STYLES[notification.type];
  const TypeIcon = typeStyle.icon;
  const isUnread = notification.status === "unread";

  const handleClick = () => {
    if (isUnread) {
      onMarkRead?.(notification.id);
    }
  };

  const content = (
    <div className="flex w-full items-start gap-3 p-4 text-left">
      <span
        className={cn(
          "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
          typeStyle.iconClassName,
        )}
      >
        <TypeIcon className="h-4 w-4" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-start justify-between gap-2">
          <span className="text-sm font-medium">{notification.title}</span>
          <span className="shrink-0 text-xs text-muted-foreground">
            {formatNotificationTimestamp(notification.created_at)}
          </span>
        </span>
        <span className="mt-0.5 block text-sm text-muted-foreground">{notification.message}</span>
      </span>
      {isUnread ? (
        <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-destructive" aria-label="Unread" />
      ) : null}
    </div>
  );

  return (
<div
      className={cn(
        "group relative border-b border-white/10 transition-colors",
        isUnread ? "bg-muted/30 hover:bg-muted/50" : "hover:bg-muted/20",
      )}
    >
      {notification.link ? (
        <Link to={notification.link} onClick={handleClick} className="flex w-full" data-testid={`notification-link-${notification.id}`}>
          {content}
        </Link>
      ) : (
        <button type="button" onClick={handleClick} className="flex w-full" data-testid={`notification-item-${notification.id}`}>
          {content}
        </button>
      )}
      {onDelete ? (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-1 top-1 h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100"
          onClick={() => onDelete(notification.id)}
          aria-label={`Delete notification: ${notification.title}`}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      ) : null}
    </div>
  );
}