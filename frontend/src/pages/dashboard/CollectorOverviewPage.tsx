import { Link } from "react-router-dom";
import { ClipboardList, Image, Layers3, PackageCheck, RefreshCcw, Timer, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { PickupCard } from "@/components/dashboard/PickupCard";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { CollectorPickupActions } from "@/components/dashboard/CollectorPickupActions";
import {
  useAssignedCollectorRequests,
  useAvailableCollectorRequests,
  useCollectorSummary,
} from "@/hooks/useCollectorRequests";

function RefreshButton({
  isFetching,
  onRefresh,
}: {
  isFetching: boolean;
  onRefresh: () => void;
}) {
  return (
    <Button
      type="button"
      variant="outline"
      className="gap-2"
      disabled={isFetching}
      onClick={onRefresh}
      aria-busy={isFetching}
    >
      <RefreshCcw
        className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`}
        aria-hidden="true"
      />
      {isFetching ? "Refreshing..." : "Refresh"}
    </Button>
  );
}

function ViewDetailsLink({ requestId }: { requestId: number }) {
  return (
    <Button asChild variant="outline" className="gap-2">
      <Link to={`/collector/pickups/${requestId}`}>View Details</Link>
    </Button>
  );
}

export function CollectorOverviewPage() {
  const availableRequestsQuery = useAvailableCollectorRequests();
  const assignedRequestsQuery = useAssignedCollectorRequests();
  const summaryQuery = useCollectorSummary();

  const availableRequests = availableRequestsQuery.data ?? [];
  const assignedRequests = assignedRequestsQuery.data ?? [];
  const summary = summaryQuery.data;

  const materialTypeCount = new Set(
    availableRequests.map((request) => request.waste_type.trim().toLowerCase()),
  ).size;
  const requestsWithImages = availableRequests.filter((request) => request.image_url).length;

  const isFetching =
    availableRequestsQuery.isFetching ||
    assignedRequestsQuery.isFetching ||
    summaryQuery.isFetching;

  const refresh = () => {
    void availableRequestsQuery.refetch();
    void assignedRequestsQuery.refetch();
    void summaryQuery.refetch();
  };

  return (
    <>
      <SeoHead
        title="Collector Dashboard"
        description="Review live pickup requests, accept available jobs, and manage your assigned pickups."
        path="/collector/overview"
      />

      <PageHeader
        title="Available Pickup Requests"
        description="Live unassigned requests from the collector queue. Open a request to review its location, material details, and uploaded image."
        actions={<RefreshButton isFetching={isFetching} onRefresh={refresh} />}
      />

      <section className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
        <StatsCard
          label="Available Now"
          value={availableRequestsQuery.data ? String(availableRequests.length) : "-"}
          helper="Unassigned pickup requests currently in the collector queue."
          icon={<ClipboardList className="h-5 w-5" />}
        />
        <StatsCard
          label="Total Assigned"
          value={summary ? String(summary.total_assigned) : "-"}
          helper="Requests ever assigned to your collector account."
          icon={<Truck className="h-5 w-5" />}
        />
        <StatsCard
          label="Active Jobs"
          value={summary ? String(summary.active_jobs) : "-"}
          helper="Requests currently in progress under your account."
          icon={<Timer className="h-5 w-5" />}
        />
        <StatsCard
          label="Completed Jobs"
          value={summary ? String(summary.completed_jobs) : "-"}
          helper="Pickups you have completed and confirmed."
          icon={<PackageCheck className="h-5 w-5" />}
        />
        <StatsCard
          label="Material Types"
          value={availableRequestsQuery.data ? String(materialTypeCount) : "-"}
          helper="Distinct waste types across the currently available requests."
          icon={<Layers3 className="h-5 w-5" />}
        />
        <StatsCard
          label="Photo Attachments"
          value={availableRequestsQuery.data ? String(requestsWithImages) : "-"}
          helper="Available requests that include a citizen-provided image."
          icon={<Image className="h-5 w-5" />}
        />
      </section>

      <section className="mt-8">
        <DashboardCard
          title="Collector Queue"
          description="This list shows unassigned pickup requests. Accept one to start working on it."
        >
          {availableRequestsQuery.isPending && !availableRequestsQuery.data ? (
            <LoadingSkeleton count={3} />
          ) : availableRequestsQuery.isError ? (
            <ErrorState
              error={availableRequestsQuery.error}
              fallback="Unable to load available pickup requests. Please try again."
              onRetry={() => availableRequestsQuery.refetch()}
              isRetrying={availableRequestsQuery.isFetching}
              title="Unable to load available requests"
            />
          ) : availableRequests.length > 0 ? (
            <div className="space-y-4">
              {availableRequests.map((request) => (
                <PickupCard
                  key={request.id}
                  request={request}
                  expandable
                  footer={
                    <>
                      <CollectorPickupActions request={request} />
                      <ViewDetailsLink requestId={request.id} />
                    </>
                  }
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No pickup requests available right now"
              description="New unassigned pickup requests will appear here as citizens submit them. Pull to refresh or check back in a few minutes."
              action={
                <Button type="button" variant="outline" onClick={refresh} disabled={isFetching}>
                  <RefreshCcw
                    className={`mr-1.5 h-4 w-4 ${isFetching ? "animate-spin" : ""}`}
                    aria-hidden="true"
                  />
                  {isFetching ? "Refreshing..." : "Refresh now"}
                </Button>
              }
            />
          )}
        </DashboardCard>
      </section>

      <section className="mt-8">
        <DashboardCard
          title="My Active Pickups"
          description="Requests you are currently working on. Continue with the next available action."
        >
          {assignedRequestsQuery.isPending && !assignedRequestsQuery.data ? (
            <LoadingSkeleton count={2} />
          ) : assignedRequestsQuery.isError ? (
            <ErrorState
              error={assignedRequestsQuery.error}
              fallback="Unable to load your assigned pickup requests. Please try again."
              onRetry={() => assignedRequestsQuery.refetch()}
              isRetrying={assignedRequestsQuery.isFetching}
              title="Unable to load your active pickups"
            />
          ) : assignedRequests.length > 0 ? (
            <div className="space-y-4">
              {assignedRequests.map((request) => (
                <PickupCard
                  key={request.id}
                  request={request}
                  expandable
                  footer={
                    <>
                      <CollectorPickupActions request={request} />
                      <ViewDetailsLink requestId={request.id} />
                    </>
                  }
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No active pickups yet"
              description="Accept a request from the collector queue above to start working on it. Your in-progress pickups will appear here."
            />
          )}
        </DashboardCard>
      </section>
    </>
  );
}
