import { Clock } from "lucide-react";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/ui/button";
import {
  formatMarketplaceCurrency,
  formatMarketplaceStatus,
} from "@/lib/marketplace";
import type { MarketplaceInventoryLot } from "@/types/marketplace";

interface ReservationDialogProps {
  lot: MarketplaceInventoryLot | null;
  isOpen: boolean;
  isPending: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function ReservationDialog({
  lot,
  isOpen,
  isPending,
  onConfirm,
  onClose,
}: ReservationDialogProps) {
  if (!lot) {
    return null;
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Reserve this lot"
      description="Reserving a lot holds it for you for 24 hours while you arrange the purchase."
      footer={
        <>
          <Button type="button" variant="outline" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button type="button" onClick={onConfirm} disabled={isPending}>
            {isPending ? "Reserving..." : "Confirm reservation"}
          </Button>
        </>
      }
    >
      <dl className="space-y-3 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Material</dt>
          <dd className="text-right font-medium">
            {lot.material_description ?? lot.material_category_name}
          </dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Status</dt>
          <dd className="capitalize">{formatMarketplaceStatus(lot.status)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Weight</dt>
          <dd>{lot.weight_kg.toFixed(2)} kg</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Price / kg</dt>
          <dd>
            {formatMarketplaceCurrency(lot.unit_price_per_kg_snapshot, lot.currency_code ?? "INR")}
          </dd>
        </div>
        <div className="flex justify-between gap-4 border-t pt-3">
          <dt className="text-muted-foreground">Total value</dt>
          <dd className="font-semibold text-emerald-400">
            {formatMarketplaceCurrency(lot.total_listed_amount, lot.currency_code ?? "INR")}
          </dd>
        </div>
      </dl>
      <p className="mt-4 flex items-center gap-2 rounded-md bg-blue-500/10 px-3 py-2 text-xs text-blue-400">
        <Clock className="h-4 w-4 shrink-0" aria-hidden="true" />
        The reservation expires automatically after 24 hours if the lot is not purchased.
      </p>
    </Modal>
  );
}
