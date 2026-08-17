import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { formatMarketplaceCurrency, formatMarketplaceStatus } from "@/lib/marketplace";
import type { MarketplaceInventoryLot } from "@/types/marketplace";

interface MarketplaceInventoryTableProps {
  lots: MarketplaceInventoryLot[];
  onReserve: (id: number) => void;
  onCancelReservation: (id: number) => void;
  onPurchase: (lot: MarketplaceInventoryLot) => void;
}

export function MarketplaceInventoryTable({
  lots,
  onReserve,
  onCancelReservation,
  onPurchase,
}: MarketplaceInventoryTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#0f1117]">
      <table className="w-full text-left text-sm text-gray-300">
        <thead className="border-b border-gray-800 bg-[#161b22] text-xs uppercase text-gray-400">
          <tr>
            <th className="px-6 py-4 font-medium">Material</th>
            <th className="px-6 py-4 font-medium">City</th>
            <th className="px-6 py-4 font-medium text-right">Weight (kg)</th>
            <th className="px-6 py-4 font-medium text-right">Price/kg</th>
            <th className="px-6 py-4 font-medium text-right">Total value</th>
            <th className="px-6 py-4 font-medium">Status</th>
            <th className="px-6 py-4 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {lots.map((lot) => {
            const isReservedByMe = lot.status === "reserved" && lot.is_reserved_by_me;
            return (
              <tr key={lot.id} className="transition-colors hover:bg-white/[0.02]">
                <td className="whitespace-nowrap px-6 py-4">
                  <Link
                    to={`/dealer/marketplace/${lot.id}`}
                    className="font-medium text-gray-100 transition-colors hover:text-emerald-400"
                  >
                    {lot.material_description ?? lot.material_category_name}
                  </Link>
                  <span className="mt-0.5 block text-xs text-gray-500">
                    {lot.material_category_name}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4">{lot.source_city}</td>
                <td className="whitespace-nowrap px-6 py-4 text-right">
                  {lot.weight_kg.toFixed(2)}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right">
                  {formatMarketplaceCurrency(lot.unit_price_per_kg_snapshot, lot.currency_code ?? "INR")}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right font-medium text-emerald-400">
                  {formatMarketplaceCurrency(lot.total_listed_amount, lot.currency_code ?? "INR")}
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <span className="capitalize">
                    {isReservedByMe ? "Reserved by you" : formatMarketplaceStatus(lot.status)}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right">
                  <div className="flex justify-end gap-2">
                    {isReservedByMe ? (
                      <>
                        <Button
                          type="button"
                          size="sm"
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
                          Cancel
                        </Button>
                      </>
                    ) : lot.status === "available" ? (
                      <Button type="button" size="sm" onClick={() => onReserve(lot.id)}>
                        Reserve
                      </Button>
                    ) : null}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
