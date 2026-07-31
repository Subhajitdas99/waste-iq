import { Link } from "react-router-dom";
import {
  ArrowRight,
  CalendarPlus,
  CheckCircle2,
  ClipboardList,
  Clock3,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { EmptyState } from "@/components/EmptyState";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { PickupCard } from "@/components/dashboard/PickupCard";
import { NotificationsPanel } from "@/components/dashboard/NotificationsPanel";
import { RecyclingImpactCard } from "@/components/dashboard/RecyclingImpactCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { useAuth } from "@/context/AuthContext";
import {
  useCitizenPickupSummary,
  useCitizenPickups,
} from "@/hooks/useCitizenPickups";
import { useCitizenNotifications } from "@/hooks/useCitizenNotifications";
import { buildPickupActivityText, formatDateTime } from "@/lib/pickup";
import { computeRecyclingImpact } from "@/lib/recycling";
import { getApiErrorMessage } from "@/lib/api-error";

const quickActions = [
  {
    title: "Create pickup",
    description: "Submit a new recyclable waste pickup request with image upload.",
    href: "/dashboard/pickups/new",
  },
  {
    title: "View requests",
    description: "Track active pickups, statuses, and collector assignments.",
    href: "/dashboard/pickups",
  },
  {
    title: "Pickup history",
    description: "Review completed and cancelled requests with searchable filters.",
    href: "/dashboard/history",
  },
  {
    title: "Profile",
    description: "See your account details and current API-backed profile data.",
    href: "/dashboard/profile",
  },
];

export function DashboardOverviewPage() {
  const { user } = useAuth();
  const summaryQuery = useCitizenPickupSummary();
  const pickupsQuery = useCitizenPickups();
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllRead,
  } = useCitizenNotifications(pickupsQuery.data);

  const requests = pickupsQuery.data ?? [];
  const summary = summaryQuery.data;
  const dashboardError = pickupsQuery.error ?? summaryQuery.error;
  const isRefreshing = pickupsQuery.isFetching || summaryQuery.isFetching;
  const pendingRequests = requests.filter((request) => request.status === "pending");
  const activeRequests = requests.filter((request) =>
    ["accepted", "on_the_way", "collected"].includes(request.status),
  );
  const completedRequests = requests.filter((request) => request.status === "completed");
  const upcomingPickup = activeRequests[0] ?? pendingRequests[0] ?? null;
  const recentRequests = requests.slice(0, 4);
  const recyclingImpact = computeRecyclingImpact(requests);

  return (
    <>
      <SeoHead
        title="Citizen Dashboard"
        description="Manage Waste-IQ pickup requests, track recycling activity, and review your citizen portal history."
        path="/dashboard/overview"
      />

      <PageHeader
        title="Dashboard Overview"
        description="Track your waste pickups, monitor request progress, and keep your account ready for the next collection."
        actions={
          <Button asChild>
            <Link to="/dashboard/pickups/new">New Pickup Request</Link>
          </Button>
        }
      />

      <section className="overflow-hidden rounded-[2rem] border border-white/30 bg-gradient-to-br from-primary/15 via-card to-accent/10 p-8 shadow-xl">
        <div className="grid gap-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-primary">
              Welcome Back
            </p>
            <h2 className="mt-4 text-4xl font-bold tracking-tight">
              Hello, {user?.name ?? "Citizen"}.
            </h2>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">
              Your citizen portal is ready to create new requests, track current pickups,
              and review the environmental impact of completed collections.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild size="lg" className="gap-2 rounded-full px-7">
                <Link to="/dashboard/pickups/new">
                  Start a Pickup
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="rounded-full px-7">
                <Link to="/dashboard/pickups">Track Active Requests</Link>
              </Button>
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-white/40 bg-background/70 p-6 shadow-lg backdrop-blur">
            <p className="text-sm font-semibold text-foreground">Portal Snapshot</p>
            <div className="mt-5 space-y-4">
              <div className="flex items-center justify-between rounded-2xl bg-muted/40 px-4 py-3">
                <span className="text-sm text-muted-foreground">Member since</span>
                <span className="font-medium">{formatDateTime(user?.created_at)}</span>
              </div>
              <div className="flex items-center justify-between rounded-2xl bg-muted/40 px-4 py-3">
                <span className="text-sm text-muted-foreground">Current role</span>
                <span className="font-medium capitalize">{user?.role}</span>
              </div>
              <div className="flex items-center justify-between rounded-2xl bg-muted/40 px-4 py-3">
                <span className="text-sm text-muted-foreground">Active requests</span>
                <span className="font-medium">{activeRequests.length + pendingRequests.length}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatsCard
          label="Total Requests"
          value={summary ? String(summary.total_requests) : "-"}
          helper="All pickup requests submitted through the citizen portal."
          icon={<ClipboardList className="h-5 w-5" />}
        />
        <StatsCard
          label="Pending"
          value={summary ? String(summary.pending_requests) : "-"}
          helper="Requests waiting for collector acceptance."
          icon={<Clock3 className="h-5 w-5" />}
        />
        <StatsCard
          label="Accepted"
          value={summary ? String(summary.accepted_requests) : "-"}
          helper="Pickups that already have a collector assigned."
          icon={<Sparkles className="h-5 w-5" />}
        />
        <StatsCard
          label="Completed"
          value={summary ? String(summary.completed_requests) : "-"}
          helper="Collections successfully finished and logged."
          icon={<CheckCircle2 className="h-5 w-5" />}
        />
      </section>

      {dashboardError ? (
        <section
          role="alert"
          className="mt-6 flex flex-col gap-4 rounded-2xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between"
        >
          <span>
            {getApiErrorMessage(
              dashboardError,
              "Unable to load your pickup dashboard. Please try again.",
            )}
          </span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="self-start border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive sm:self-auto"
            disabled={isRefreshing}
            onClick={() => {
              void Promise.all([pickupsQuery.refetch(), summaryQuery.refetch()]);
            }}
          >
            {isRefreshing ? "Retrying..." : "Try again"}
          </Button>
        </section>
      ) : null}

      <section className="mt-8">
        <RecyclingImpactCard
          metrics={recyclingImpact}
          isLoading={pickupsQuery.isPending && !pickupsQuery.data}
        />
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickActions.map((action) => (
          <DashboardCard
            key={action.title}
            title={action.title}
            description={action.description}
            actions={
              <Button asChild variant="ghost" size="sm">
                <Link to={action.href}>Open</Link>
              </Button>
            }
          >
            <div className="text-sm text-muted-foreground">
              Navigate directly to the corresponding citizen workflow.
            </div>
          </DashboardCard>
        ))}
      </section>

      <section className="mt-8 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <DashboardCard
            title="Pending Pickups"
            description="Requests that can still be reviewed or cancelled before assignment."
            actions={
              <Button asChild variant="ghost" size="sm">
                <Link to="/dashboard/pickups">See all</Link>
              </Button>
            }
          >
            {pickupsQuery.isPending && !pickupsQuery.data ? (
              <LoadingSkeleton count={2} />
            ) : pendingRequests.length > 0 ? (
              <div className="space-y-4">
                {pendingRequests.slice(0, 2).map((request) => (
                  <PickupCard
                    key={request.id}
                    request={request}
                    footer={
                      <Button asChild variant="outline">
                        <Link to={`/dashboard/pickups/${request.id}`}>View Details</Link>
                      </Button>
                    }
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                title="No pending pickups"
                description="You have no pending requests right now. Create a new pickup whenever recyclables are ready."
                action={
                  <Button asChild>
                    <Link to="/dashboard/pickups/new">Create Pickup</Link>
                  </Button>
                }
              />
            )}
          </DashboardCard>

          <DashboardCard
            title="Completed Pickups"
            description="Your latest successfully completed waste collections."
            actions={
              <Button asChild variant="ghost" size="sm">
                <Link to="/dashboard/history">Open history</Link>
              </Button>
            }
          >
            {completedRequests.length > 0 ? (
              <div className="space-y-4">
                {completedRequests.slice(0, 2).map((request) => (
                  <PickupCard
                    key={request.id}
                    request={request}
                    footer={
                      <Button asChild variant="outline">
                        <Link to={`/dashboard/pickups/${request.id}`}>View Record</Link>
                      </Button>
                    }
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                title="No completed pickups yet"
                description="Completed pickups will appear here after collectors finish the full collection flow."
              />
            )}
          </DashboardCard>
        </div>

        <div className="space-y-6">
          <DashboardCard
            title="Upcoming Pickup"
            description="Your next active or queued request in the current backend queue."
          >
            {upcomingPickup ? (
              <PickupCard
                request={upcomingPickup}
                footer={
                  <Button asChild variant="outline">
                    <Link to={`/dashboard/pickups/${upcomingPickup.id}`}>Track Pickup</Link>
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={<CalendarPlus className="h-8 w-8" />}
                title="Nothing scheduled yet"
                description="Once you create a pickup request, the next active item will appear here."
              />
            )}
          </DashboardCard>

          <DashboardCard
            title="Recent Activity"
            description="A lightweight feed based on your most recent pickup requests."
          >
            {recentRequests.length > 0 ? (
              <div className="space-y-4">
                {recentRequests.map((request) => (
                  <div
                    key={request.id}
                    className="rounded-2xl border bg-muted/20 px-4 py-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium">Request #{request.id}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDateTime(request.created_at)}
                      </p>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {buildPickupActivityText(request)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No recent activity"
                description="Your first pickup request will start populating this activity feed."
              />
            )}
          </DashboardCard>

          <DashboardCard
            title="Notifications"
            description="Status updates detected from your pickup requests."
          >
            <NotificationsPanel
              notifications={notifications}
              unreadCount={unreadCount}
              isLoading={pickupsQuery.isPending && !pickupsQuery.data}
              onMarkAsRead={markAsRead}
              onMarkAllRead={markAllRead}
            />
          </DashboardCard>
        </div>
      </section>
    </>
  );
}
