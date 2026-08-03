import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useDeleteNotification,
  useMarkAllRead,
  useMarkRead,
  useUnreadNotifications,
} from "@/hooks/useNotifications";
import { NotificationBadge } from "./NotificationBadge";
import { NotificationList } from "./NotificationList";

const MAX_PREVIEW = 5;

interface NotificationDropdownProps {
  notificationsPath: string;
}

export function NotificationDropdown({ notificationsPath }: NotificationDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const { data: unreadNotifications } = useUnreadNotifications();
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();
  const deleteNotification = useDeleteNotification();

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node | null;
      if (containerRef.current && !containerRef.current.contains(target)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const preview = (unreadNotifications ?? []).slice(0, MAX_PREVIEW);
  const hasNotifications = (unreadNotifications?.length ?? 0) > 0;

  return (
    <div ref={containerRef} className="relative" data-testid="notification-dropdown">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen((current) => !current)}
        aria-label="Open notifications"
        aria-expanded={isOpen}
      >
        <NotificationBadge />
      </Button>

      {isOpen ? (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border bg-card shadow-xl sm:w-96">
          <div className="flex items-center justify-between gap-2 border-b border-white/10 px-4 py-3">
            <div>
              <p className="text-sm font-semibold">Unread notifications</p>
              <p className="text-xs text-muted-foreground">
                {unreadNotifications?.length ?? 0} unread
              </p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="gap-1.5"
              onClick={() => markAllRead.mutate()}
              disabled={!hasNotifications || markAllRead.isPending}
            >
              <CheckCheck className="h-4 w-4" />
              Mark all read
            </Button>
          </div>

          <div className="max-h-96 overflow-y-auto">
            <NotificationList
              notifications={preview}
              onMarkRead={(id) => markRead.mutate(id)}
              onDelete={(id) => deleteNotification.mutate(id)}
              emptyTitle="You're all caught up"
              emptyDescription="No unread notifications right now."
            />
          </div>

          <div className="border-t border-white/10 p-2">
            <Button
              asChild
              type="button"
              variant="ghost"
              className="w-full justify-between gap-2"
              onClick={() => setIsOpen(false)}
            >
              <Link to={notificationsPath}>
                View all notifications
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}