import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArchiveRestore } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { PickupCard } from "@/components/dashboard/PickupCard";
import { SearchBar } from "@/components/dashboard/SearchBar";
import { FilterPanel } from "@/components/dashboard/FilterPanel";
import { Pagination } from "@/components/dashboard/Pagination";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { useCitizenPickups } from "@/hooks/useCitizenPickups";
import { getApiErrorMessage } from "@/lib/api-error";
import { matchesPickupQuery, sortPickupRequests } from "@/lib/pickup";
import type { PickupFilters } from "@/types/pickup";

const PAGE_SIZE = 5;

export function PickupHistoryPage() {
  const pickupsQuery = useCitizenPickups();
  const [filters, setFilters] = useState<PickupFilters>({
    query: "",
    status: "all",
    sort: "newest",
  });
  const [currentPage, setCurrentPage] = useState(1);

  const historyRequests = (pickupsQuery.data ?? []).filter((request) =>
    ["completed", "cancelled"].includes(request.status),
  );

  const filteredRequests = sortPickupRequests(
    historyRequests.filter((request) => {
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

  useEffect(() => {
    setCurrentPage(1);
  }, [filters.query, filters.sort, filters.status]);

  return (
    <>
      <SeoHead
        title="Pickup History"
        description="Review completed and cancelled Waste-IQ pickup requests with search, filters, and expandable history cards."
        path="/dashboard/history"
      />

      <PageHeader
        title="Pickup History"
        description="Search through completed and cancelled pickup requests using expandable cards and client-side pagination."
      />

      <DashboardCard
        title="History Filters"
        description="Filter previous requests by status, search terms, and sort order."
      >
        <div className="space-y-4">
          <SearchBar
            value={filters.query}
            onChange={(query) => setFilters((current) => ({ ...current, query }))}
            placeholder="Search historical pickups"
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
        <div className="mt-6 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {getApiErrorMessage(pickupsQuery.error, "Unable to load pickup history.")}
        </div>
      ) : filteredRequests.length > 0 ? (
        <div className="mt-6 space-y-4">
          {paginatedRequests.map((request) => (
            <PickupCard
              key={request.id}
              request={request}
              expandable
              footer={
                <Button asChild variant="outline">
                  <Link to={`/dashboard/pickups/${request.id}`}>Open Record</Link>
                </Button>
              }
            />
          ))}

          <Pagination
            currentPage={safePage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      ) : (
        <div className="mt-6">
          <EmptyState
            icon={<ArchiveRestore className="h-8 w-8" />}
            title="No pickup history yet"
            description="Completed and cancelled requests will appear here after your citizen portal activity grows."
            action={
              <Button asChild>
                <Link to="/dashboard/pickups/new">Create Pickup</Link>
              </Button>
            }
          />
        </div>
      )}
    </>
  );
}
