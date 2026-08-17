import { useState } from "react";
import { DealerApprovalGate } from "@/components/dashboard/DealerApprovalGate";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { Pagination } from "@/components/dashboard/Pagination";
import { TransactionHistoryTable } from "@/components/dashboard/TransactionHistoryTable";
import { EmptyState } from "@/components/EmptyState";
import {
  useMarketplaceOrders,
  useMarketplaceTransactions,
} from "@/hooks/useMarketplace";
import {
  formatMarketplaceCurrency,
  formatMarketplaceDateTime,
} from "@/lib/marketplace";
import type { MarketplaceTransactionType } from "@/types/marketplace";

const PAGE_SIZE = 20;

export default function OrderHistoryPage() {
  const [ordersPage, setOrdersPage] = useState(1);
  const [transactionsPage, setTransactionsPage] = useState(1);
  const [transactionType, setTransactionType] = useState<MarketplaceTransactionType | "">("");
  const [activeTab, setActiveTab] = useState<"orders" | "transactions">("orders");

  const ordersQuery = useMarketplaceOrders(ordersPage, PAGE_SIZE);
  const transactionsQuery = useMarketplaceTransactions(
    transactionsPage,
    PAGE_SIZE,
    transactionType || undefined,
  );

  return (
    <DealerApprovalGate>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Order History</h1>
          <p className="text-sm text-gray-400">
            Review your completed purchases and marketplace transaction history.
          </p>
        </div>

        <div className="flex gap-1 rounded-lg border border-gray-800 bg-[#0f1117] p-1 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab("orders")}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "orders"
                ? "bg-emerald-500 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Orders
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("transactions")}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "transactions"
                ? "bg-emerald-500 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Transactions
          </button>
        </div>

        {activeTab === "orders" ? (
          <>
            <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#0f1117]">
              <table className="w-full text-left text-sm text-gray-300">
                <thead className="border-b border-gray-800 bg-[#161b22] text-xs uppercase text-gray-400">
                  <tr>
                    <th className="px-6 py-4 font-medium">Order</th>
                    <th className="px-6 py-4 font-medium">Material</th>
                    <th className="px-6 py-4 font-medium text-right">Weight (kg)</th>
                    <th className="px-6 py-4 font-medium text-right">Amount</th>
                    <th className="px-6 py-4 font-medium">Status</th>
                    <th className="px-6 py-4 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {ordersQuery.isLoading ? (
                    <tr>
                      <td colSpan={6}>
                        <LoadingSkeleton count={2} />
                      </td>
                    </tr>
                  ) : (ordersQuery.data?.items ?? []).length === 0 ? (
                    <tr>
                      <td colSpan={6}>
                        <EmptyState
                          title="No orders yet"
                          description="When you purchase inventory lots, your orders will appear here."
                          className="border-0"
                        />
                      </td>
                    </tr>
                  ) : (
                    (ordersQuery.data?.items ?? []).map((order) => (
                      <tr key={order.id} className="transition-colors hover:bg-white/[0.02]">
                        <td className="whitespace-nowrap px-6 py-4 font-medium text-emerald-400">
                          {order.order_number}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          {order.material_description ?? order.material_category_name}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-right">
                          {order.quantity_kg.toFixed(2)}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-right font-medium text-emerald-400">
                          {formatMarketplaceCurrency(order.total_amount, order.currency_code)}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium capitalize text-emerald-400">
                            {order.status}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-gray-400">
                          {formatMarketplaceDateTime(order.created_at)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {ordersQuery.data && ordersQuery.data.total_pages > 1 && (
              <Pagination
                currentPage={ordersPage}
                totalPages={ordersQuery.data.total_pages}
                onPageChange={setOrdersPage}
              />
            )}
          </>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <label htmlFor="transaction-type" className="text-sm font-medium text-gray-300">
                Filter by type:
              </label>
              <select
                id="transaction-type"
                value={transactionType}
                onChange={(e) => {
                  setTransactionType(e.target.value as MarketplaceTransactionType | "");
                  setTransactionsPage(1);
                }}
                className="rounded-md border border-gray-700 bg-[#161b22] px-3 py-1.5 text-sm text-gray-200 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">All types</option>
                <option value="reservation">Reservation</option>
                <option value="purchase">Purchase</option>
                <option value="cancellation">Cancellation</option>
                <option value="reservation_expired">Reservation expired</option>
              </select>
            </div>

            <TransactionHistoryTable
              transactions={transactionsQuery.data?.items ?? []}
              isLoading={transactionsQuery.isLoading}
            />

            {transactionsQuery.data && transactionsQuery.data.total_pages > 1 && (
              <Pagination
                currentPage={transactionsPage}
                totalPages={transactionsQuery.data.total_pages}
                onPageChange={setTransactionsPage}
              />
            )}
          </>
        )}
      </div>
    </DealerApprovalGate>
  );
}
