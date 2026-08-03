import { Bell } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";

interface EmptyNotificationsProps {
  title?: string;
  description?: string;
}

export function EmptyNotifications({
  title = "No notifications yet",
  description = "Updates about pickups, inventory, and account activity will appear here.",
}: EmptyNotificationsProps) {
  return <EmptyState icon={<Bell className="h-6 w-6" />} title={title} description={description} />;
}