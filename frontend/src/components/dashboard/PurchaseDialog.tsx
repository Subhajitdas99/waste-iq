import { CheckCircle2 } from "lucide-react";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/ui/button";
import { formatMarketplaceCurrency } from "@/lib/marketplace";
import type { MarketplaceInventoryLot, MarketplaceOrderDetail } from "@/types/marketplace";

interface PurchaseDialogProps {
  lot: MarketplaceInventoryLot | null;
  isOpen: boolean;
  isPending: boolean;
  order: MarketplaceOrderDetail | null;
  onConfirm: () => void;
  onClose: () => void;
}

export function PurchaseDialog({
  lot,
  isOpen,
  isPending,
  order,
  onConfirm,
  onClose,
}: PurchaseDialogProps) {
  if (!lot) {
    return null;
  }

  if (order) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title="Purchase complete"
        description="The lot has been added to your order history."
        footer={
          <Button type="button" onClick={onClose}>
            Done
          </Button>
        }
      >
        <div className="flex flex-col items-center gap-3 py-2 text-center">
          <CheckCircle2 className="h-12 w-12 text-emerald-400" aria-hidden="true" />
          <p className="text-sm text-muted-foreground">
            Order <span className="font-semibold text-foreground">{order.order_number}</span>{" "}
            was created successfully for{" "}
            {formatMarketplaceCurrency(order.total_amount, order.currency_code)}.
          </p>
        </div>
      </Modal>
    );
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Confirm purchase"
      description="This will complete the purchase and move the lot to your order history."
      footer={
        <>
          <Button type="button" variant="outline" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button type="button" onClick={onConfirm} disabled={isPending}>
            {isPending ? "Purchasing..." : "Confirm purchase"}
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
          <dt className="text-muted-foreground">Seller</dt>
          <dd className="text-right">{lot.seller_name ?? "—"}</dd>
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
          <dt className="text-muted-foreground">Amount due</dt>
          <dd className="font-semibold text-emerald-400">
            {formatMarketplaceCurrency(lot.total_listed_amount, lot.currency_code ?? "INR")}
          </dd>
        </div>
      </dl>
    </Modal>
  );
}
