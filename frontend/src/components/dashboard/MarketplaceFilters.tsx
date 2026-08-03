import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface MarketplaceFiltersState {
  search: string;
  city: string;
  category: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
}

interface MarketplaceFiltersProps {
  filters: MarketplaceFiltersState;
  categories: string[];
  onFiltersChange: (filters: MarketplaceFiltersState) => void;
  onApply: () => void;
  onReset: () => void;
}

export function MarketplaceFilters({
  filters,
  categories,
  onFiltersChange,
  onApply,
  onReset,
}: MarketplaceFiltersProps) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-gray-800 bg-[#0f1117] p-4 lg:flex-row lg:items-end">
      <div className="flex-1">
        <label htmlFor="marketplace-search" className="mb-1.5 block text-xs font-medium text-gray-400">
          Search
        </label>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" aria-hidden="true" />
          <Input
            id="marketplace-search"
            value={filters.search}
            onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
            placeholder="Search by material or description..."
            className="pl-9"
          />
        </div>
      </div>

      <div>
        <label htmlFor="marketplace-category" className="mb-1.5 block text-xs font-medium text-gray-400">
          Category
        </label>
        <select
          id="marketplace-category"
          value={filters.category}
          onChange={(e) => onFiltersChange({ ...filters, category: e.target.value })}
          className="h-10 w-full rounded-md border border-gray-700 bg-[#161b22] px-3 text-sm text-gray-200 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 lg:w-44"
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="marketplace-city" className="mb-1.5 block text-xs font-medium text-gray-400">
          City
        </label>
        <Input
          id="marketplace-city"
          value={filters.city}
          onChange={(e) => onFiltersChange({ ...filters, city: e.target.value })}
          placeholder="e.g. Kolkata"
          className="lg:w-44"
        />
      </div>

      <div>
        <label htmlFor="marketplace-sort" className="mb-1.5 block text-xs font-medium text-gray-400">
          Sort by
        </label>
        <select
          id="marketplace-sort"
          value={filters.sortBy}
          onChange={(e) => {
            const [sortBy, sortOrder] = e.target.value.split(":") as [string, "asc" | "desc"];
            onFiltersChange({ ...filters, sortBy, sortOrder });
          }}
          className="h-10 w-full rounded-md border border-gray-700 bg-[#161b22] px-3 text-sm text-gray-200 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 lg:w-48"
        >
          <option value="created_at:desc">Newest first</option>
          <option value="total_listed_amount:desc">Highest value</option>
          <option value="total_listed_amount:asc">Lowest value</option>
          <option value="weight_kg:desc">Heaviest</option>
          <option value="weight_kg:asc">Lightest</option>
        </select>
      </div>

      <div className="flex gap-2">
        <Button type="button" onClick={onApply}>
          Apply filters
        </Button>
        <Button type="button" variant="outline" onClick={onReset}>
          Reset
        </Button>
      </div>
    </div>
  );
}
