import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { PickupCard } from "@/components/dashboard/PickupCard";
import { SearchBar } from "@/components/dashboard/SearchBar";
import { FilterPanel } from "@/components/dashboard/FilterPanel";
import { Pagination } from "@/components/dashboard/Pagination";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { ConfirmationDialog } from "@/components/dashboard/ConfirmationDialog";
import { useCancelCitizenPickup, useCitizenPickups } from "@/hooks/useCitizenPickups";
import { matchesPickupQuery, sortPickupRequests } from "@/lib/pickup";
import type { PickupFilters } from "@/types/pickup";

const PAGE_SIZE = 6;

export function CitizenPickupsPage() {
  const pickupsQuery = useCitizenPickups();
  const cancelPickupMutation = useCancelCitizenPickup();
  const [filters, setFilters] = useState<PickupFilters>({
    query: "",
    status: "all",
    sort: "newest",
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [pickupToCancel, setPickupToCancel] = useState<number | null>(null);

  const requests = pickupsQuery.data ?? [];
  const filteredRequests = sortPickupRequests(
    requests.filter((request) => {
      const statusMatches =
        filters.status === "all" ? true : request.status === filters.status;
      return statusMatches && matchesPickupQuery(request, filters.query);
    }),
    filters.sort,
  );

  const totalPages = Math.max(1, Math.ceil(filteredRequests.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const pageStart = (safePage - 1) * PAGE_SIZE;
  const paginatedRequests = filteredRequests.slice(pageStart, pageStart + PAGE_SIZE);

  const isFilterActive = filters.query.trim() !== "" || filters.status !== "all";

  useEffect(() => {
    setCurrentPage(1);
  }, [filters.query, filters.sort, filters.status]);

  return (
    <>
      <SeoHead
        title="My Pickups"
        description="Search, filter, and manage all citizen pickup requests in Waste-IQ."
        path="/dashboard/pickups"
      />

      <PageHeader
        title="My Pickup Requests"
        description="Review all requests, open request details, and cancel pending pickups before assignment."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              className="gap-2"
              onClick={() => pickupsQuery.refetch()}
              disabled={pickupsQuery.isFetching}
              aria-busy={pickupsQuery.isFetching}
            >
              <RefreshCcw
                className={`h-4 w-4 ${pickupsQuery.isFetching ? "animate-spin" : ""}`}
                aria-hidden="true"
              />
              {pickupsQuery.isFetching ? "Refreshing..." : "Refresh"}
            </Button>
            <Button asChild className="gap-2">
              <Link to="/dashboard/pickups/new">
                <Plus className="h-4 w-4" />
                New Request
              </Link>
            </Button>
          </div>
        }
      />

      <DashboardCard
        title="Search and Filters"
        description="Search across waste types, collector names, addresses, and request IDs."
      >
        <div className="space-y-4">
          <SearchBar
            value={filters.query}
            onChange={(query) => setFilters((current) => ({ ...current, query }))}
          />
          <FilterPanel
            status={filters.status}
            sort={filters.sort}
            onStatusChange={(status) => setFilters((current) => ({ ...current, status }))}
            onSortChange={(sort) => setFilters((current) => ({ ...current, sort }))}
          />
        </div>
      </DashboardCard>

      {pickupsQuery.isPending && !pickupsQuery.data ? (
        <div className="mt-6">
          <LoadingSkeleton count={3} />
        </div>
      ) : pickupsQuery.isError ? (
        <div className="mt-6">
          <ErrorState
            error={pickupsQuery.error}
            fallback="Unable to load your pickup requests."
            onRetry={() => pickupsQuery.refetch()}
            isRetrying={pickupsQuery.isFetching}
            title="Unable to load pickup requests"
          />
        </div>
      ) : filteredRequests.length > 0 ? (
        <div className="mt-6 space-y-4">
          {paginatedRequests.map((request) => (
            <PickupCard
              key={request.id}
              request={request}
              footer={
                <>
                  <Button asChild variant="outline">
                    <Link to={`/dashboard/pickups/${request.id}`}>View Details</Link>
                  </Button>
                  {request.can_cancel ? (
                    <Button
                      type="button"
                      variant="destructive"
                      onClick={() => setPickupToCancel(request.id)}
                    >
                      Cancel Request
                    </Button>
                  ) : null}
                </>
              }
            />
          ))}

          <Pagination
            currentPage={safePage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      ) : requests.length === 0 ? (
        <div className="mt-6">
          <EmptyState
            title="You haven't created a pickup yet"
            description="Submit a new recyclable waste pickup request to track it here. You can also attach a photo for AI classification."
            action={
              <Button asChild>
                <Link to="/dashboard/pickups/new">Create Your First Pickup</Link>
              </Button>
            }
          />
        </div>
      ) : (
        <div className="mt-6">
          <EmptyState
            title="No matching pickups"
            description="Try changing your search term or status filter to see more results."
            action={
              isFilterActive ? (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() =>
                    setFilters({ query: "", status: "all", sort: filters.sort })
                  }
                >
                  Clear filters
                </Button>
              ) : null
            }
          />
        </div>
      )}

      <ConfirmationDialog
        isOpen={pickupToCancel !== null}
        title="Cancel pickup request"
        description="Only pending pickup requests can be cancelled. After cancellation, you cannot undo this action."
        confirmLabel="Yes, Cancel Pickup"
        cancelLabel="Keep Request"
        isPending={cancelPickupMutation.isPending}
        onClose={() => setPickupToCancel(null)}
        onConfirm={async () => {
          if (pickupToCancel === null) {
            return;
          }
          await cancelPickupMutation.mutateAsync(pickupToCancel);
          setPickupToCancel(null);
        }}
      />
    </>
  );
}
