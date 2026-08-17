import { useEffect, useRef, useState } from "react";
import { AlertCircle, CheckCheck, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Pagination } from "@/components/dashboard/Pagination";
import {
  useDeleteNotification,
  useDeleteRead,
  useMarkAllRead,
  useMarkRead,
  useNotifications,
} from "@/hooks/useNotifications";
import type { NotificationStatus } from "@/types/notification";
import {
  NotificationFilter,
  type NotificationFilterValue,
} from "./NotificationFilter";
import { NotificationList } from "./NotificationList";

const PAGE_SIZE = 10;

interface NotificationCenterProps {
  title?: string;
  description?: string;
}

export function NotificationCenter({
  title = "Notifications",
  description = "View updates about your pickups, inventory, and account activity.",
}: NotificationCenterProps) {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<NotificationFilterValue>("all");
  const listRef = useRef<HTMLDivElement | null>(null);

  const status: NotificationStatus | undefined =
    filter === "all" ? undefined : filter;

  const { data, isLoading, isError } = useNotifications(page, PAGE_SIZE, status);
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();
  const deleteNotification = useDeleteNotification();
  const deleteRead = useDeleteRead();

  const notifications = data?.items ?? [];
  const totalPages = data?.total_pages ?? 0;
  const hasUnread = notifications.some((notification) => notification.status === "unread");
  const hasRead = notifications.some((notification) => notification.status === "read");

  useEffect(() => {
    if (!isLoading && listRef.current) {
      listRef.current.scrollIntoView?.({ behavior: "smooth", block: "start" });
    }
  }, [page, isLoading]);

  const handleFilterChange = (nextFilter: NotificationFilterValue) => {
    setFilter(nextFilter);
    setPage(1);
  };

  const hasItems = !isLoading && notifications.length > 0;

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <CardTitle>{title}</CardTitle>
          <CardDescription>
            {description} {data ? `(${data.total_items} total)` : null}
          </CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <NotificationFilter value={filter} onChange={handleFilterChange} />
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => markAllRead.mutate()}
            disabled={!hasUnread || markAllRead.isPending}
          >
            <CheckCheck className="h-4 w-4" />
            Mark all read
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => deleteRead.mutate()}
            disabled={!hasRead || deleteRead.isPending}
          >
            <Trash2 className="h-4 w-4" />
            Clear read
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0" ref={listRef}>
        {isError ? (
          <div className="flex items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            We couldn't load your notifications. Please try again.
          </div>
        ) : (
          <NotificationList
            notifications={notifications}
            isLoading={isLoading}
            onMarkRead={(id) => markRead.mutate(id)}
            onDelete={(id) => deleteNotification.mutate(id)}
          />
        )}

        {hasItems ? (
          <div className="pt-2">
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}