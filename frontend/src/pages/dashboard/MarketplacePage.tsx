import { useEffect, useRef, useState } from "react";
import { LayoutGrid, List, Store } from "lucide-react";
import { DealerApprovalGate } from "@/components/dashboard/DealerApprovalGate";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { MarketplaceFilters, type MarketplaceFiltersState } from "@/components/dashboard/MarketplaceFilters";
import { MarketplaceInventoryCard } from "@/components/dashboard/MarketplaceInventoryCard";
import { MarketplaceInventoryTable } from "@/components/dashboard/MarketplaceInventoryTable";
import { Pagination } from "@/components/dashboard/Pagination";
import { PurchaseDialog } from "@/components/dashboard/PurchaseDialog";
import { ReservationDialog } from "@/components/dashboard/ReservationDialog";
import { Toast } from "@/components/Toast";
import { EmptyState } from "@/components/EmptyState";
import {
  useCancelReservation,
  useMarketplaceInventory,
  usePurchaseInventory,
  useReserveInventory,
} from "@/hooks/useMarketplace";
import type {
  MarketplaceInventoryLot,
  MarketplaceInventoryQuery,
  MarketplaceOrderDetail,
} from "@/types/marketplace";

const PAGE_SIZE = 12;
const INITIAL_FILTERS: MarketplaceFiltersState = {
  search: "",
  city: "",
  category: "",
  sortBy: "created_at",
  sortOrder: "desc",
};

interface ToastState {
  message: string;
  type: "success" | "error";
}

type ViewMode = "grid" | "table";

export default function MarketplacePage() {
  const [page, setPage] = useState(1);
  const [draftFilters, setDraftFilters] = useState<MarketplaceFiltersState>(INITIAL_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<MarketplaceFiltersState>(INITIAL_FILTERS);
  const [reserveTarget, setReserveTarget] = useState<MarketplaceInventoryLot | null>(null);
  const [purchaseTarget, setPurchaseTarget] = useState<MarketplaceInventoryLot | null>(null);
  const [purchaseOrder, setPurchaseOrder] = useState<MarketplaceOrderDetail | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

  const query: MarketplaceInventoryQuery = {
    page,
    page_size: PAGE_SIZE,
    sort_by: appliedFilters.sortBy,
    sort_order: appliedFilters.sortOrder,
    search: appliedFilters.search || undefined,
    city: appliedFilters.city || undefined,
  };

  const { data, isLoading } = useMarketplaceInventory(query);
  const reserveMutation = useReserveInventory();
  const cancelMutation = useCancelReservation();
  const purchaseMutation = usePurchaseInventory();

  useEffect(() => {
    return () => {
      if (toastTimeoutRef.current !== null) {
        window.clearTimeout(toastTimeoutRef.current);
      }
    };
  }, []);

  const showToast = (message: string, type: ToastState["type"]) => {
    setToast({ message, type });
    if (toastTimeoutRef.current !== null) {
      window.clearTimeout(toastTimeoutRef.current);
    }
    toastTimeoutRef.current = window.setTimeout(() => setToast(null), 5000);
  };

  const handleApplyFilters = () => {
    setPage(1);
    setAppliedFilters(draftFilters);
  };

  const handleResetFilters = () => {
    setPage(1);
    setDraftFilters(INITIAL_FILTERS);
    setAppliedFilters(INITIAL_FILTERS);
  };

  const handleReserve = (id: number) => {
    reserveMutation.mutate(id, {
      onSuccess: () => {
        setReserveTarget(null);
        showToast("Lot reserved successfully for 24 hours.", "success");
      },
    });
  };

  const handleCancelReservation = (id: number) => {
    cancelMutation.mutate(id, {
      onSuccess: () => {
        showToast("Reservation cancelled successfully.", "success");
      },
    });
  };

  const handleOpenPurchase = (lot: MarketplaceInventoryLot) => {
    setPurchaseOrder(null);
    setPurchaseTarget(lot);
  };

  const handlePurchase = () => {
    if (!purchaseTarget) {
      return;
    }
    purchaseMutation.mutate(purchaseTarget.id, {
      onSuccess: (order) => {
        setPurchaseOrder(order);
        showToast("Purchase completed successfully.", "success");
      },
    });
  };

  const categories = Array.from(
    new Set((data?.items ?? []).map((lot) => lot.material_category_name).filter(Boolean)),
  ).sort();

  return (
    <DealerApprovalGate>
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}

      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Marketplace Listings</h1>
          <p className="text-sm text-gray-400">
            Browse recyclable inventory lots, reserve what you need, and purchase materials.
          </p>
        </div>

        <MarketplaceFilters
          filters={draftFilters}
          categories={categories}
          onFiltersChange={setDraftFilters}
          onApply={handleApplyFilters}
          onReset={handleResetFilters}
        />

        <div className="flex items-center justify-between gap-3">
          <p className="text-sm text-gray-400">
            {data ? `${data.total_items} lot${data.total_items === 1 ? "" : "s"} available` : ""}
          </p>
          <div className="flex gap-1 rounded-lg border border-gray-800 bg-[#0f1117] p-1">
            <button
              type="button"
              onClick={() => setViewMode("grid")}
              aria-label="Grid view"
              aria-pressed={viewMode === "grid"}
              className={`rounded-md p-1.5 transition-colors ${
                viewMode === "grid" ? "bg-emerald-500 text-white" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <LayoutGrid className="h-4 w-4" aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              aria-label="Table view"
              aria-pressed={viewMode === "table"}
              className={`rounded-md p-1.5 transition-colors ${
                viewMode === "table" ? "bg-emerald-500 text-white" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <List className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>

        {isLoading ? (
          <LoadingSkeleton count={4} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            icon={<Store className="h-10 w-10" aria-hidden="true" />}
            title="No inventory available"
            description="There are no available inventory lots matching your filters. Try adjusting the filters or check back later."
          />
        ) : viewMode === "grid" ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {data.items.map((lot) => (
              <MarketplaceInventoryCard
                key={lot.id}
                lot={lot}
                onReserve={() => setReserveTarget(lot)}
                onCancelReservation={handleCancelReservation}
                onPurchase={handleOpenPurchase}
              />
            ))}
          </div>
        ) : (
          <MarketplaceInventoryTable
            lots={data.items}
            onReserve={(id) => {
              const lot = data.items.find((item) => item.id === id);
              if (lot) {
                setReserveTarget(lot);
              }
            }}
            onCancelReservation={handleCancelReservation}
            onPurchase={handleOpenPurchase}
          />
        )}

        {data && data.total_pages > 1 && (
          <Pagination currentPage={page} totalPages={data.total_pages} onPageChange={setPage} />
        )}
      </div>

      <ReservationDialog
        lot={reserveTarget}
        isOpen={reserveTarget !== null}
        isPending={reserveMutation.isPending}
        onConfirm={() => reserveTarget && handleReserve(reserveTarget.id)}
        onClose={() => setReserveTarget(null)}
      />

      <PurchaseDialog
        lot={purchaseTarget}
        isOpen={purchaseTarget !== null}
        isPending={purchaseMutation.isPending}
        order={purchaseOrder}
        onConfirm={handlePurchase}
        onClose={() => {
          setPurchaseTarget(null);
          setPurchaseOrder(null);
        }}
      />
    </DealerApprovalGate>
  );
}
