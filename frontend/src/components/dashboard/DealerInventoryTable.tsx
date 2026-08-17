import { DealerInventory } from "@/types/dealerInventory";
import { StatusBadge } from "./StatusBadge";

interface DealerInventoryTableProps {
  inventory: DealerInventory[];
  isLoading: boolean;
  onReserve: (id: number) => void;
  onRelease: (id: number) => void;
  onMarkSold: (id: number) => void;
  onDelete: (id: number) => void;
}

export default function DealerInventoryTable({
  inventory,
  isLoading,
  onReserve,
  onRelease,
  onMarkSold,
  onDelete,
}: DealerInventoryTableProps) {
  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-gray-800 bg-[#0f1117]">
        <div className="text-gray-400">Loading inventory...</div>
      </div>
    );
  }

  if (inventory.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-gray-800 bg-[#0f1117]">
        <div className="text-gray-400">No inventory found.</div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#0f1117]">
      <table className="w-full text-left text-sm text-gray-300">
        <thead className="border-b border-gray-800 bg-[#161b22] text-xs uppercase text-gray-400">
          <tr>
            <th className="px-6 py-4 font-medium">Material</th>
            <th className="px-6 py-4 font-medium">Category</th>
            <th className="px-6 py-4 font-medium text-right">Quantity (kg)</th>
            <th className="px-6 py-4 font-medium text-right">Price/kg</th>
            <th className="px-6 py-4 font-medium text-right">Total Value</th>
            <th className="px-6 py-4 font-medium">Status</th>
            <th className="px-6 py-4 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {inventory.map((item) => (
            <tr
              key={item.id}
              className="transition-colors hover:bg-white/[0.02]"
            >
              <td className="whitespace-nowrap px-6 py-4 font-medium text-gray-100">
                {item.material_type}
                {item.quality_grade && (
                  <span className="ml-2 rounded bg-gray-800 px-2 py-0.5 text-xs text-gray-400">
                    Grade {item.quality_grade}
                  </span>
                )}
              </td>
              <td className="whitespace-nowrap px-6 py-4">
                {item.category}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-right">
                {item.quantity_kg.toFixed(2)}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-right">
                ₹{Number(item.price_per_kg).toFixed(2)}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-right font-medium text-emerald-400">
                ₹{Number(item.total_value).toFixed(2)}
              </td>
              <td className="whitespace-nowrap px-6 py-4">
                <StatusBadge status={item.status} />
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-right">
                <div className="flex justify-end gap-2">
                  {item.status === "available" && (
                    <>
                      <button
                        onClick={() => onReserve(item.id)}
                        className="rounded bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-400 transition-colors hover:bg-blue-500/20"
                      >
                        Reserve
                      </button>
                      <button
                        onClick={() => onDelete(item.id)}
                        className="rounded bg-red-500/10 px-3 py-1 text-xs font-medium text-red-400 transition-colors hover:bg-red-500/20"
                      >
                        Delete
                      </button>
                    </>
                  )}
                  {item.status === "reserved" && (
                    <>
                      <button
                        onClick={() => onRelease(item.id)}
                        className="rounded bg-gray-500/10 px-3 py-1 text-xs font-medium text-gray-400 transition-colors hover:bg-gray-500/20"
                      >
                        Release
                      </button>
                      <button
                        onClick={() => onMarkSold(item.id)}
                        className="rounded bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 transition-colors hover:bg-emerald-500/20"
                      >
                        Mark Sold
                      </button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
