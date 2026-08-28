import type { PickupStatus } from "@/types/pickup";

export const PICKUP_MARKER_COLORS: Record<PickupStatus, string> = {
  pending: "#f59e0b",
  accepted: "#0ea5e9",
  on_the_way: "#06b6d4",
  collected: "#14b8a6",
  weight_recorded: "#6366f1",
  disputed: "#f59e0b",
  completed: "#10b981",
  cancelled: "#f43f5e",
};

export function pickupMarkerColor(status: string): string {
  return PICKUP_MARKER_COLORS[status as PickupStatus] ?? PICKUP_MARKER_COLORS.pending;
}

export const COLLECTOR_MARKER_COLOR = "#6366f1";