import type {
  PickupRequest,
  PickupStatus,
  PickupTimelineEvent,
} from "@/types/pickup";

export const PICKUP_STATUS_FLOW: PickupStatus[] = [
  "pending",
  "accepted",
  "on_the_way",
  "collected",
  "completed",
];

export const pickupStatusConfig: Record<
  PickupStatus,
  { label: string; badgeClassName: string; dotClassName: string }
> = {
  pending: {
    label: "Pending",
    badgeClassName:
      "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300",
    dotClassName: "bg-amber-500",
  },
  accepted: {
    label: "Accepted",
    badgeClassName:
      "border-sky-500/20 bg-sky-500/10 text-sky-700 dark:text-sky-300",
    dotClassName: "bg-sky-500",
  },
  on_the_way: {
    label: "On The Way",
    badgeClassName:
      "border-cyan-500/20 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300",
    dotClassName: "bg-cyan-500",
  },
  collected: {
    label: "Collected",
    badgeClassName:
      "border-teal-500/20 bg-teal-500/10 text-teal-700 dark:text-teal-300",
    dotClassName: "bg-teal-500",
  },
  completed: {
    label: "Completed",
    badgeClassName:
      "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
    dotClassName: "bg-emerald-500",
  },
  cancelled: {
    label: "Cancelled",
    badgeClassName:
      "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-300",
    dotClassName: "bg-rose-500",
  },
};

export function formatPickupStatus(status: string): string {
  if (status in pickupStatusConfig) {
    return pickupStatusConfig[status as PickupStatus].label;
  }
  return status.replace(/_/g, " ");
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  }).format(new Date(value));
}

export function formatWeight(weightKg: number | null | undefined): string {
  if (typeof weightKg !== "number") {
    return "Not reported";
  }

  return `${weightKg.toFixed(1)} kg`;
}

export function getPickupProgress(status: PickupStatus): number {
  if (status === "cancelled") {
    return 0;
  }

  const index = PICKUP_STATUS_FLOW.indexOf(status);
  if (index < 0) {
    return 0;
  }

  return Math.round(((index + 1) / PICKUP_STATUS_FLOW.length) * 100);
}

export function buildPickupActivityText(request: PickupRequest): string {
  switch (request.status) {
    case "completed":
      return `Pickup completed for ${request.waste_type}.`;
    case "collected":
      return `Waste collected and awaiting final confirmation.`;
    case "on_the_way":
      return `${request.assigned_collector_name ?? "Your collector"} is on the way.`;
    case "accepted":
      return `${request.assigned_collector_name ?? "A collector"} accepted your request.`;
    case "cancelled":
      return `Pickup request was cancelled.`;
    default:
      return `Pickup request submitted for ${request.waste_type}.`;
  }
}

export function sortPickupRequests(
  requests: PickupRequest[],
  sort: "newest" | "oldest" | "status",
): PickupRequest[] {
  return [...requests].sort((left, right) => {
    if (sort === "oldest") {
      return new Date(left.created_at).getTime() - new Date(right.created_at).getTime();
    }

    if (sort === "status") {
      return formatPickupStatus(left.status).localeCompare(formatPickupStatus(right.status));
    }

    return new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
  });
}

export function matchesPickupQuery(request: PickupRequest, query: string): boolean {
  if (!query.trim()) {
    return true;
  }

  const normalizedQuery = query.trim().toLowerCase();
  return [
    request.waste_type,
    request.address,
    request.category ?? "",
    request.assigned_collector_name ?? "",
    String(request.id),
  ].some((value) => value.toLowerCase().includes(normalizedQuery));
}

export function filterTimelinePreview(
  timeline: PickupTimelineEvent[],
  limit = 3,
): PickupTimelineEvent[] {
  return [...timeline]
    .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())
    .slice(0, limit);
}
