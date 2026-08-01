import { useState } from "react";
import { Link } from "react-router-dom";
import {
  useDealerStockList,
  useReserveDealerStock,
  useReleaseDealerStock,
  useMarkDealerStockSold,
  useDeleteDealerStock,
} from "@/hooks/useDealerStock";
import DealerInventoryTable from "@/components/dashboard/DealerInventoryTable";
import { Pagination } from "@/components/dashboard/Pagination";

export default function DealerInventoryPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const { data, isLoading } = useDealerStockList(page, 20, statusFilter || undefined);
  const reserveMutation = useReserveDealerStock();
  const releaseMutation = useReleaseDealerStock();
  const markSoldMutation = useMarkDealerStockSold();
  const deleteMutation = useDeleteDealerStock();

  const handleReserve = (id: number) => {
    reserveMutation.mutate(id);
  };

  const handleRelease = (id: number) => {
    releaseMutation.mutate(id);
  };

  const handleMarkSold = (id: number) => {
    markSoldMutation.mutate(id);
  };

  const handleDelete = (id: number) => {
    if (window.confirm("Are you sure you want to delete this inventory item?")) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            My Inventory
          </h1>
          <p className="text-sm text-gray-400">
            Manage your collected recyclable materials
          </p>
        </div>
        <Link
          to="/dashboard/dealer/marketplace"
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-[#0a0c10]"
        >
          Browse Marketplace
        </Link>
      </div>

      <div className="flex items-center justify-between rounded-lg border border-gray-800 bg-[#0f1117] p-4">
        <div className="flex items-center gap-4">
          <label htmlFor="status" className="text-sm font-medium text-gray-300">
            Status Filter:
          </label>
          <select
            id="status"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="rounded-md border border-gray-700 bg-[#161b22] px-3 py-1.5 text-sm text-gray-200 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">All Statuses</option>
            <option value="available">Available</option>
            <option value="reserved">Reserved</option>
            <option value="sold">Sold</option>
          </select>
        </div>
        <div className="text-sm text-gray-400">
          Total Items: {data?.total_items || 0}
        </div>
      </div>

      <DealerInventoryTable
        inventory={data?.items || []}
        isLoading={isLoading}
        onReserve={handleReserve}
        onRelease={handleRelease}
        onMarkSold={handleMarkSold}
        onDelete={handleDelete}
      />

      {data && data.total_pages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={data.total_pages}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
