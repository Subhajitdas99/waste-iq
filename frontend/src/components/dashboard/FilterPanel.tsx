import type { PickupStatus } from "@/types/pickup";

interface FilterPanelProps {
  status: "all" | PickupStatus;
  sort: "newest" | "oldest" | "status";
  onStatusChange: (value: "all" | PickupStatus) => void;
  onSortChange: (value: "newest" | "oldest" | "status") => void;
}

export function FilterPanel({
  status,
  sort,
  onStatusChange,
  onSortChange,
}: FilterPanelProps) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <label className="space-y-2 text-sm">
        <span className="font-medium text-foreground">Status</span>
        <select
          value={status}
          onChange={(event) => onStatusChange(event.target.value as "all" | PickupStatus)}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <option value="all">All statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="on_the_way">On the way</option>
          <option value="collected">Collected</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </label>

      <label className="space-y-2 text-sm">
        <span className="font-medium text-foreground">Sort by</span>
        <select
          value={sort}
          onChange={(event) =>
            onSortChange(event.target.value as "newest" | "oldest" | "status")
          }
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="status">Status</option>
        </select>
      </label>
    </div>
  );
}
