import type { PickupRequest } from "@/types/pickup";

export interface RecyclingImpactMetrics {
  totalWeightKg: number;
  totalPickups: number;
  co2SavedKg: number;
  ecoPoints: number;
}

export const CO2_SAVED_PER_KG = 0.42;
export const ECO_POINTS_PER_KG = 10;

function roundTo(value: number, decimals = 1): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

export function computeRecyclingImpact(requests: PickupRequest[]): RecyclingImpactMetrics {
  const completedRequests = requests.filter((request) => request.status === "completed");
  const totalWeightKg = completedRequests.reduce(
    (sum, request) => sum + (request.assignment?.weight_kg ?? 0),
    0,
  );

  return {
    totalWeightKg: roundTo(totalWeightKg),
    totalPickups: completedRequests.length,
    co2SavedKg: roundTo(totalWeightKg * CO2_SAVED_PER_KG),
    ecoPoints: roundTo(totalWeightKg * ECO_POINTS_PER_KG, 0),
  };
}

export function formatImpactNumber(value: number): string {
  return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
}
