import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { NotificationCenter } from "@/components/dashboard/notifications/NotificationCenter";
import { useAuth } from "@/context/AuthContext";
import { getPortalConfig } from "@/lib/portal";

export default function NotificationsPage() {
  const { user } = useAuth();
  const routePrefix = getPortalConfig(user?.role ?? "citizen").routePrefix;

  return (
    <>
      <SeoHead
        title="Notifications"
        description="View updates about your pickups, inventory, and account activity."
        path={`${routePrefix}/notifications`}
      />

      <PageHeader
        title="Notifications"
        description="Stay up to date with your pickup requests, dealer status, and inventory activity."
      />

      <NotificationCenter />
    </>
  );
}