import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { DealerApprovalGate } from "@/components/dashboard/DealerApprovalGate";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { PurchaseDialog } from "@/components/dashboard/PurchaseDialog";
import { Toast } from "@/components/Toast";
import { Button } from "@/components/ui/button";
import {
  useCancelReservation,
  useMarketplaceItem,
  usePurchaseInventory,
  useReserveInventory,
} from "@/hooks/useMarketplace";
import {
  formatMarketplaceCurrency,
  formatMarketplaceDateTime,
  formatMarketplaceStatus,
  formatReservationCountdown,
} from "@/lib/marketplace";
import type { MarketplaceOrderDetail } from "@/types/marketplace";

interface ToastState {
  message: string;
  type: "success" | "error";
}

export default function MarketplaceDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const lotId = Number(id);
  const { data: lot, isLoading, isError } = useMarketplaceItem(lotId);
  const reserveMutation = useReserveInventory();
  const cancelMutation = useCancelReservation();
  const purchaseMutation = usePurchaseInventory();
  const [isPurchaseOpen, setIsPurchaseOpen] = useState(false);
  const [purchaseOrder, setPurchaseOrder] = useState<MarketplaceOrderDetail | null>(null);
  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

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

  if (isLoading) {
    return (
      <DealerApprovalGate>
        <LoadingSkeleton variant="detail" />
      </DealerApprovalGate>
    );
  }

  if (isError || !lot) {
    return (
      <DealerApprovalGate>
        <div className="rounded-3xl border bg-muted/20 p-8 text-center">
          <h2 className="text-xl font-semibold tracking-tight">Inventory lot not found</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
            This lot is unavailable. It may have been sold or reserved by another dealer.
          </p>
          <Button asChild className="mt-6">
            <Link to="/dealer/marketplace">Back to marketplace</Link>
          </Button>
        </div>
      </DealerApprovalGate>
    );
  }

  const isReservedByMe = lot.status === "reserved" && lot.is_reserved_by_me;

  return (
    <DealerApprovalGate>
      {toast && <Toast message={toast.message} type={toast.type} onDismiss={() => setToast(null)} />}

      <div className="space-y-6">
        <Link
          to="/dealer/marketplace"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-gray-200"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to marketplace
        </Link>

        <div className="rounded-3xl border bg-[#0f1117] p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-widest text-gray-500">{lot.lot_number}</p>
              <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
                {lot.material_description ?? lot.material_category_name}
              </h1>
              <p className="mt-1 text-sm text-gray-400">{lot.material_category_name}</p>
            </div>
            <span className="w-fit rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium capitalize text-emerald-400">
              {isReservedByMe ? "Reserved by you" : formatMarketplaceStatus(lot.status)}
            </span>
          </div>

          <dl className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="rounded-xl border border-gray-800 bg-[#161b22] p-4">
              <dt className="text-xs text-gray-500">Weight</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-100">
                {lot.weight_kg.toFixed(2)} kg
              </dd>
            </div>
            <div className="rounded-xl border border-gray-800 bg-[#161b22] p-4">
              <dt className="text-xs text-gray-500">Price per kg</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-100">
                {formatMarketplaceCurrency(lot.unit_price_per_kg_snapshot, lot.currency_code ?? "INR")}
              </dd>
            </div>
            <div className="rounded-xl border border-gray-800 bg-[#161b22] p-4">
              <dt className="text-xs text-gray-500">Total value</dt>
              <dd className="mt-1 text-lg font-semibold text-emerald-400">
                {formatMarketplaceCurrency(lot.total_listed_amount, lot.currency_code ?? "INR")}
              </dd>
            </div>
            <div className="rounded-xl border border-gray-800 bg-[#161b22] p-4">
              <dt className="text-xs text-gray-500">Seller</dt>
              <dd className="mt-1 text-gray-100">{lot.seller_name ?? "—"}</dd>
            </div>
            <div className="rounded-xl border border-gray-800 bg-[#161b22] p-4">
              <dt className="text-xs text-gray-500">Source city</dt>
              <dd className="mt-1 text-gray-100">{lot.source_city}</dd>
            </div>
            <div className="rounded-xl border border-gray-800 bg-[#161b22] p-4">
              <dt className="text-xs text-gray-500">Listed on</dt>
              <dd className="mt-1 text-gray-100">{formatMarketplaceDateTime(lot.created_at)}</dd>
            </div>
          </dl>

          {isReservedByMe && (
            <div className="mt-4 rounded-xl border border-blue-500/30 bg-blue-500/10 px-4 py-3 text-sm text-blue-300">
              You hold a reservation on this lot that expires in{" "}
              <span className="font-semibold">
                {formatReservationCountdown(lot.reservation_expires_at)}
              </span>
              . Complete the purchase before it expires or the lot becomes available again.
            </div>
          )}

          <div className="mt-6 flex flex-wrap gap-3 border-t border-gray-800 pt-6">
            {isReservedByMe ? (
              <>
                <Button
                  type="button"
                  disabled={purchaseMutation.isPending}
                  onClick={() => {
                    setPurchaseOrder(null);
                    setIsPurchaseOpen(true);
                  }}
                >
                  Buy now
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={cancelMutation.isPending}
                  onClick={() =>
                    cancelMutation.mutate(lot.id, {
                      onSuccess: () => showToast("Reservation cancelled successfully.", "success"),
                    })
                  }
                >
                  Cancel reservation
                </Button>
              </>
            ) : lot.status === "available" ? (
              <Button
                type="button"
                disabled={reserveMutation.isPending}
                onClick={() =>
                  reserveMutation.mutate(lot.id, {
                    onSuccess: () =>
                      showToast("Lot reserved successfully for 24 hours.", "success"),
                  })
                }
              >
                Reserve this lot
              </Button>
            ) : null}
          </div>
        </div>
      </div>

      <PurchaseDialog
        lot={lot}
        isOpen={isPurchaseOpen}
        isPending={purchaseMutation.isPending}
        order={purchaseOrder}
        onConfirm={() =>
          purchaseMutation.mutate(lot.id, {
            onSuccess: (order) => {
              setPurchaseOrder(order);
              showToast("Purchase completed successfully.", "success");
            },
          })
        }
        onClose={() => {
          setIsPurchaseOpen(false);
          setPurchaseOrder(null);
        }}
      />
    </DealerApprovalGate>
  );
}
