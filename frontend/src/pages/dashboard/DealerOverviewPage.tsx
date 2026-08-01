import { useEffect, useState } from "react";
import { Boxes, Layers3, MapPinned, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { Pagination } from "@/components/dashboard/Pagination";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { DealerApprovalGate } from "@/components/dashboard/DealerApprovalGate";
import { useDealerInventory } from "@/hooks/useDealerInventory";
import { getApiErrorMessage } from "@/lib/api-error";
import { formatDateTime, formatWeight } from "@/lib/pickup";

const PAGE_SIZE = 12;

export function DealerOverviewPage() {
  const [page, setPage] = useState(1);
  const inventoryQuery = useDealerInventory({ page, page_size: PAGE_SIZE });
  const inventory = inventoryQuery.data;
  const lots = inventory?.items ?? [];
  const categoryCount = new Set(lots.map((lot) => lot.material_category_id)).size;
  const cityCount = new Set(lots.map((lot) => lot.source_city.trim().toLowerCase())).size;
  const listedWeight = lots.reduce((total, lot) => total + lot.weight_kg, 0);

  useEffect(() => {
    if (inventory && inventory.total_pages > 0 && page > inventory.total_pages) {
      setPage(inventory.total_pages);
    }
  }, [inventory, page]);

  return (
    <DealerApprovalGate>
      <SeoHead
        title="Dealer Inventory"
        description="Browse live, available recyclable inventory lots in the Waste-IQ dealer marketplace."
        path="/dealer/overview"
      />

      <PageHeader
        title="Available Inventory"
        description="Marketplace lots currently available to your approved dealer account."
        actions={
          <Button
            type="button"
            variant="outline"
            className="gap-2"
            disabled={inventoryQuery.isFetching}
            onClick={() => {
              void inventoryQuery.refetch();
            }}
          >
            <RefreshCcw className="h-4 w-4" />
            {inventoryQuery.isFetching ? "Refreshing..." : "Refresh"}
          </Button>
        }
      />

      <section className="grid gap-4 md:grid-cols-3">
        <StatsCard
          label="Available Lots"
          value={inventory ? String(inventory.total_items) : "-"}
          helper="Total available marketplace lots returned by the backend."
          icon={<Boxes className="h-5 w-5" />}
        />
        <StatsCard
          label="Categories on This Page"
          value={inventory ? String(categoryCount) : "-"}
          helper="Distinct material categories in the current server page."
          icon={<Layers3 className="h-5 w-5" />}
        />
        <StatsCard
          label="Listed Weight on This Page"
          value={inventory ? formatWeight(listedWeight) : "-"}
          helper="Combined weight of the lots currently displayed."
          icon={<MapPinned className="h-5 w-5" />}
        />
      </section>

      <section className="mt-8">
        <DashboardCard
          title="Marketplace Lots"
          description="Live data from GET /dealer/inventory-lots. Pricing currency is available on the individual lot-detail API, so this list does not assume one."
        >
          {inventoryQuery.isPending && !inventory ? (
            <LoadingSkeleton count={3} />
          ) : inventoryQuery.isError ? (
            <div
              role="alert"
              className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              {getApiErrorMessage(
                inventoryQuery.error,
                "Unable to load dealer inventory. Please try again.",
              )}
            </div>
          ) : lots.length > 0 ? (
            <div className="space-y-4">
              <div className="grid gap-4 lg:grid-cols-2">
                {lots.map((lot) => (
                  <article
                    key={lot.id}
                    className="rounded-3xl border bg-muted/20 p-5 transition-colors hover:bg-muted/35"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                          Lot #{lot.id}
                        </p>
                        <h2 className="mt-2 text-xl font-semibold">
                          {lot.material_category_name}
                        </h2>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {lot.material_description ?? "No additional material description provided."}
                        </p>
                      </div>
                      <span className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium capitalize text-primary">
                        {lot.status.replace(/_/g, " ")}
                      </span>
                    </div>

                    <dl className="mt-5 grid gap-4 sm:grid-cols-3">
                      <div>
                        <dt className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                          Weight
                        </dt>
                        <dd className="mt-1 font-medium">{formatWeight(lot.weight_kg)}</dd>
                      </div>
                      <div>
                        <dt className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                          Source City
                        </dt>
                        <dd className="mt-1 font-medium">{lot.source_city}</dd>
                      </div>
                      <div>
                        <dt className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                          Listed
                        </dt>
                        <dd className="mt-1 font-medium">{formatDateTime(lot.created_at)}</dd>
                      </div>
                    </dl>
                  </article>
                ))}
              </div>

              {inventory ? (
                <div className="flex flex-col gap-4 rounded-2xl border bg-muted/20 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-muted-foreground">
                    Showing {lots.length} lots across {cityCount} {cityCount === 1 ? "city" : "cities"}.
                  </p>
                  <Pagination
                    currentPage={inventory.page}
                    totalPages={inventory.total_pages}
                    onPageChange={setPage}
                  />
                </div>
              ) : null}
            </div>
          ) : (
            <EmptyState
              title="No inventory lots are available"
              description="Available marketplace inventory will appear here once completed pickups are listed."
            />
          )}
        </DashboardCard>
      </section>
    </DealerApprovalGate>
  );
}
