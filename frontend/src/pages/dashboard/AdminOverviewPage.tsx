import { useState } from "react";
import { BarChart3, RefreshCcw, ShieldCheck, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { DealerApprovalDialog } from "@/components/dashboard/DealerApprovalDialog";
import {
  useAdminAnalytics,
  useAdminDealers,
  useAdminUsers,
  useApproveDealer,
  usePendingAdminDealers,
  useRejectDealer,
} from "@/hooks/useAdminDashboard";
import { getApiErrorMessage } from "@/lib/api-error";
import { formatDateTime, formatWeight } from "@/lib/pickup";
import type { AdminDealerSummary } from "@/types/admin";

function formatRole(role: string): string {
  return role.charAt(0).toUpperCase() + role.slice(1);
}

function getApprovalClassName(status: string): string {
  switch (status) {
    case "approved":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
    case "rejected":
      return "border-destructive/20 bg-destructive/10 text-destructive";
    default:
      return "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300";
  }
}

type ReviewDialogState =
  | { dealer: AdminDealerSummary; mode: "approve" | "reject" }
  | null;

export function AdminOverviewPage() {
  const [reviewDialog, setReviewDialog] = useState<ReviewDialogState>(null);
  const analyticsQuery = useAdminAnalytics();
  const usersQuery = useAdminUsers();
  const dealersQuery = useAdminDealers();
  const pendingQuery = usePendingAdminDealers();
  const approveMutation = useApproveDealer();
  const rejectMutation = useRejectDealer();
  const analytics = analyticsQuery.data;
  const users = usersQuery.data ?? [];
  const pendingDealers = pendingQuery.data?.items ?? [];
  const isRefreshing =
    analyticsQuery.isFetching ||
    usersQuery.isFetching ||
    dealersQuery.isFetching ||
    pendingQuery.isFetching;
  const isPending = approveMutation.isPending || rejectMutation.isPending;

  const handleConfirmReview = (reason?: string) => {
    if (!reviewDialog) {
      return;
    }
    const { dealer, mode } = reviewDialog;
    if (mode === "approve") {
      approveMutation.mutate(dealer.user_id);
    } else if (reason) {
      rejectMutation.mutate({ dealerUserId: dealer.user_id, reason });
    }
    setReviewDialog(null);
  };

  return (
    <>
      <SeoHead
        title="Admin Dashboard"
        description="Monitor Waste-IQ platform analytics, user records, and dealer approval data."
        path="/admin/overview"
      />

      <PageHeader
        title="Platform Overview"
        description="Live platform analytics, newest users, and dealer approval records from the admin API."
        actions={
          <Button
            type="button"
            variant="outline"
            className="gap-2"
            disabled={isRefreshing}
            onClick={() => {
              void Promise.all([
                analyticsQuery.refetch(),
                usersQuery.refetch(),
                dealersQuery.refetch(),
                pendingQuery.refetch(),
              ]);
            }}
          >
            <RefreshCcw className="h-4 w-4" />
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatsCard
          label="Total Users"
          value={analytics ? String(analytics.total_users) : "-"}
          helper="All registered platform accounts."
          icon={<Users className="h-5 w-5" />}
        />
        <StatsCard
          label="Pickup Requests"
          value={analytics ? String(analytics.total_pickup_requests) : "-"}
          helper="All pickup requests created across the platform."
          icon={<BarChart3 className="h-5 w-5" />}
        />
        <StatsCard
          label="Completed Pickups"
          value={analytics ? String(analytics.total_completed_pickups) : "-"}
          helper="Requests with a completed collection workflow."
          icon={<ShieldCheck className="h-5 w-5" />}
        />
        <StatsCard
          label="Collected Weight"
          value={analytics ? formatWeight(analytics.total_collected_weight_kg) : "-"}
          helper="Total completed collection weight reported by collectors."
          icon={<BarChart3 className="h-5 w-5" />}
        />
      </section>

      {analyticsQuery.isError ? (
        <div
          role="alert"
          className="mt-6 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
        >
          {getApiErrorMessage(
            analyticsQuery.error,
            "Unable to load platform analytics. Please try again.",
          )}
        </div>
      ) : null}

      <section className="mt-8 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <DashboardCard
          title="Request Pipeline"
          description="Live pickup request status breakdown from GET /admin/analytics."
        >
          {analyticsQuery.isPending && !analytics ? (
            <LoadingSkeleton count={2} />
          ) : analytics ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(analytics.requests_by_status).map(([status, count]) => (
                <div key={status} className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    {status.replace(/_/g, " ")}
                  </p>
                  <p className="mt-2 text-2xl font-bold">{count}</p>
                </div>
              ))}
            </div>
          ) : null}
        </DashboardCard>

        <DashboardCard
          title="Accounts by Role"
          description="Role distribution from the same authoritative analytics response."
        >
          {analyticsQuery.isPending && !analytics ? (
            <LoadingSkeleton count={2} />
          ) : analytics ? (
            <div className="space-y-3">
              {Object.entries(analytics.users_by_role).map(([role, count]) => (
                <div
                  key={role}
                  className="flex items-center justify-between rounded-2xl border bg-muted/20 px-4 py-3"
                >
                  <span className="font-medium">{formatRole(role)}</span>
                  <span className="text-xl font-bold">{count}</span>
                </div>
              ))}
            </div>
          ) : null}
        </DashboardCard>
      </section>

      <section className="mt-8 grid gap-6 xl:grid-cols-2">
        <DashboardCard
          title="Newest Users"
          description="The six most recently created records from GET /admin/users."
        >
          {usersQuery.isPending && !usersQuery.data ? (
            <LoadingSkeleton count={2} />
          ) : usersQuery.isError ? (
            <div role="alert" className="text-sm text-destructive">
              {getApiErrorMessage(usersQuery.error, "Unable to load users.")}
            </div>
          ) : users.length > 0 ? (
            <div className="space-y-3">
              {users.slice(0, 6).map((user) => (
                <div
                  key={user.id}
                  className="flex flex-col gap-2 rounded-2xl border bg-muted/20 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-medium">{user.name}</p>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                  <div className="text-sm sm:text-right">
                    <p className="font-medium capitalize">{user.role}</p>
                    <p className="text-muted-foreground">{formatDateTime(user.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No users found" description="User records will appear here once accounts are created." />
          )}
        </DashboardCard>

        <DashboardCard
          title="Dealer Review Queue"
          description={`Dealers currently awaiting approval. ${pendingDealers.length} ${pendingDealers.length === 1 ? "profile" : "profiles"} need review.`}
        >
          {pendingQuery.isPending && !pendingQuery.data ? (
            <LoadingSkeleton count={2} />
          ) : pendingQuery.isError ? (
            <div role="alert" className="text-sm text-destructive">
              {getApiErrorMessage(pendingQuery.error, "Unable to load dealer records.")}
            </div>
          ) : pendingDealers.length > 0 ? (
            <div className="space-y-3">
              {pendingDealers.map((dealer) => (
                <div key={dealer.user_id} className="rounded-2xl border bg-muted/20 p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-medium">{dealer.business_name ?? dealer.user_name}</p>
                      <p className="text-sm text-muted-foreground">{dealer.user_email}</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {dealer.city ?? "City not provided"} - {dealer.postal_code ?? "no postal code"} -{" "}
                        {dealer.profile_completion}% profile complete
                      </p>
                    </div>
                    <span
                      className={`w-fit rounded-full border px-3 py-1 text-xs font-semibold capitalize ${getApprovalClassName(dealer.approval_status)}`}
                    >
                      {dealer.has_profile ? dealer.approval_status : "Profile missing"}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      disabled={isPending || !dealer.has_profile}
                      onClick={() => setReviewDialog({ dealer, mode: "approve" })}
                    >
                      Approve
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="destructive"
                      disabled={isPending || !dealer.has_profile}
                      onClick={() => setReviewDialog({ dealer, mode: "reject" })}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No dealers awaiting approval"
              description="New dealer applications will appear here once submitted."
            />
          )}
        </DashboardCard>
      </section>

      {reviewDialog ? (
        <DealerApprovalDialog
          isOpen
          mode={reviewDialog.mode}
          dealerName={reviewDialog.dealer.business_name ?? reviewDialog.dealer.user_name}
          isPending={isPending}
          onConfirm={handleConfirmReview}
          onClose={() => setReviewDialog(null)}
        />
      ) : null}
    </>
  );
}
