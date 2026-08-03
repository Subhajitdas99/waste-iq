import { formatMarketplaceCurrency, formatMarketplaceDateTime, formatMarketplaceStatus } from "@/lib/marketplace";
import type { MarketplaceTransaction } from "@/types/marketplace";

const TYPE_STYLES: Record<string, string> = {
  reservation: "bg-blue-500/10 text-blue-400",
  cancellation: "bg-amber-500/10 text-amber-400",
  purchase: "bg-emerald-500/10 text-emerald-400",
  reservation_expired: "bg-gray-500/10 text-gray-400",
};

interface TransactionHistoryTableProps {
  transactions: MarketplaceTransaction[];
  isLoading: boolean;
}

export function TransactionHistoryTable({
  transactions,
  isLoading,
}: TransactionHistoryTableProps) {
  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-gray-800 bg-[#0f1117]">
        <div className="text-gray-400">Loading transactions...</div>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-gray-800 bg-[#0f1117]">
        <div className="text-gray-400">No transactions yet.</div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#0f1117]">
      <table className="w-full text-left text-sm text-gray-300">
        <thead className="border-b border-gray-800 bg-[#161b22] text-xs uppercase text-gray-400">
          <tr>
            <th className="px-6 py-4 font-medium">Type</th>
            <th className="px-6 py-4 font-medium">Material</th>
            <th className="px-6 py-4 font-medium text-right">Weight (kg)</th>
            <th className="px-6 py-4 font-medium text-right">Amount</th>
            <th className="px-6 py-4 font-medium">Order</th>
            <th className="px-6 py-4 font-medium">Date</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {transactions.map((transaction) => (
            <tr key={transaction.id} className="transition-colors hover:bg-white/[0.02]">
              <td className="whitespace-nowrap px-6 py-4">
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${
                    TYPE_STYLES[transaction.transaction_type] ?? "bg-gray-500/10 text-gray-400"
                  }`}
                >
                  {formatMarketplaceStatus(transaction.transaction_type)}
                </span>
              </td>
              <td className="whitespace-nowrap px-6 py-4">
                {transaction.material_category_name || transaction.lot_number}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-right">
                {transaction.quantity_kg.toFixed(2)}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-right font-medium text-emerald-400">
                {formatMarketplaceCurrency(transaction.total_amount, transaction.currency_code)}
              </td>
              <td className="whitespace-nowrap px-6 py-4">
                {transaction.order_id ? `#${transaction.order_id}` : "—"}
              </td>
              <td className="whitespace-nowrap px-6 py-4 text-gray-400">
                {formatMarketplaceDateTime(transaction.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
