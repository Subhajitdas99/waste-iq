import { ClipboardList, Image, Layers3, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { PickupCard } from "@/components/dashboard/PickupCard";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { useAvailableCollectorRequests } from "@/hooks/useCollectorRequests";
import { getApiErrorMessage } from "@/lib/api-error";

export function CollectorOverviewPage() {
  const availableRequestsQuery = useAvailableCollectorRequests();
  const availableRequests = availableRequestsQuery.data ?? [];
  const materialTypeCount = new Set(
    availableRequests.map((request) => request.waste_type.trim().toLowerCase()),
  ).size;
  const requestsWithImages = availableRequests.filter((request) => request.image_url).length;

  return (
    <>
      <SeoHead
        title="Collector Dashboard"
        description="Review live, unassigned recyclable pickup requests available to your Waste-IQ collector account."
        path="/collector/overview"
      />

      <PageHeader
        title="Available Pickup Requests"
        description="Live unassigned requests from the collector queue. Open a request to review its location, material details, and uploaded image."
        actions={
          <Button
            type="button"
            variant="outline"
            className="gap-2"
            disabled={availableRequestsQuery.isFetching}
            onClick={() => {
              void availableRequestsQuery.refetch();
            }}
          >
            <RefreshCcw className="h-4 w-4" />
            {availableRequestsQuery.isFetching ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />

      <section className="grid gap-4 md:grid-cols-3">
        <StatsCard
          label="Available Now"
          value={availableRequestsQuery.data ? String(availableRequests.length) : "-"}
          helper="Unassigned pickup requests currently in the collector queue."
          icon={<ClipboardList className="h-5 w-5" />}
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
          description="This list is backed by GET /collector/available and excludes assigned or non-pending requests."
        >
          {availableRequestsQuery.isPending && !availableRequestsQuery.data ? (
            <LoadingSkeleton count={3} />
          ) : availableRequestsQuery.isError ? (
            <div
              role="alert"
              className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              {getApiErrorMessage(
                availableRequestsQuery.error,
                "Unable to load available pickup requests. Please try again.",
              )}
            </div>
          ) : availableRequests.length > 0 ? (
            <div className="space-y-4">
              {availableRequests.map((request) => (
                <PickupCard key={request.id} request={request} expandable />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No pickup requests are available"
              description="New unassigned pickup requests will appear here as citizens submit them."
            />
          )}
        </DashboardCard>
      </section>
    </>
  );
}
