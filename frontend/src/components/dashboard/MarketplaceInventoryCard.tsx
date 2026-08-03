import { Link } from "react-router-dom";
import { Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  formatMarketplaceCurrency,
  formatMarketplaceStatus,
  formatReservationCountdown,
} from "@/lib/marketplace";
import type { MarketplaceInventoryLot } from "@/types/marketplace";
import { cn } from "@/lib/utils";

interface MarketplaceInventoryCardProps {
  lot: MarketplaceInventoryLot;
  onReserve: (id: number) => void;
  onCancelReservation: (id: number) => void;
  onPurchase: (lot: MarketplaceInventoryLot) => void;
}

export function MarketplaceInventoryCard({
  lot,
  onReserve,
  onCancelReservation,
  onPurchase,
}: MarketplaceInventoryCardProps) {
  const isReservedByMe = lot.status === "reserved" && lot.is_reserved_by_me;

  return (
    <article className="flex flex-col rounded-lg border border-gray-800 bg-[#0f1117] p-5 transition-colors hover:border-gray-700">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-medium text-gray-100">
            {lot.material_description ?? lot.material_category_name}
          </h3>
          <p className="mt-0.5 text-xs text-gray-500">{lot.material_category_name}</p>
        </div>
        <span
          className={cn(
            "rounded-full px-2.5 py-1 text-xs font-medium capitalize",
            isReservedByMe
              ? "bg-blue-500/10 text-blue-400"
              : lot.status === "available"
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-gray-500/10 text-gray-400",
          )}
        >
          {isReservedByMe ? "Reserved by you" : formatMarketplaceStatus(lot.status)}
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-xs text-gray-500">Weight</dt>
          <dd className="mt-0.5 text-gray-200">{lot.weight_kg.toFixed(2)} kg</dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Price / kg</dt>
          <dd className="mt-0.5 text-gray-200">
            {formatMarketplaceCurrency(lot.unit_price_per_kg_snapshot, lot.currency_code ?? "INR")}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Total value</dt>
          <dd className="mt-0.5 font-medium text-emerald-400">
            {formatMarketplaceCurrency(lot.total_listed_amount, lot.currency_code ?? "INR")}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">City</dt>
          <dd className="mt-0.5 text-gray-200">{lot.source_city}</dd>
        </div>
      </dl>

      {isReservedByMe && lot.reservation_expires_at && (
        <p className="mt-3 rounded bg-blue-500/10 px-3 py-1.5 text-xs text-blue-400">
          Reservation: {formatReservationCountdown(lot.reservation_expires_at)}
        </p>
      )}

      <div className="mt-4 flex items-center gap-2 border-t border-gray-800 pt-4">
        {isReservedByMe ? (
          <>
            <Button
              type="button"
              size="sm"
              className="flex-1"
              onClick={() => onPurchase(lot)}
            >
              Buy now
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => onCancelReservation(lot.id)}
            >
              Cancel reservation
            </Button>
          </>
        ) : lot.status === "available" ? (
          <Button
            type="button"
            size="sm"
            className="flex-1"
            onClick={() => onReserve(lot.id)}
          >
            Reserve
          </Button>
        ) : (
          <span className="flex-1 text-center text-xs text-gray-500">Not available</span>
        )}
        <Link
          to={`/dealer/marketplace/${lot.id}`}
          className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-gray-400 transition-colors hover:text-gray-200"
        >
          <Package className="h-3.5 w-3.5" aria-hidden="true" />
          Details
        </Link>
      </div>
    </article>
  );
}
