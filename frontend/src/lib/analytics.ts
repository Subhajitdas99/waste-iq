import type { MaterialBreakdown } from "@/types/analytics";

export const MATERIAL_LABELS: Record<keyof MaterialBreakdown, string> = {
  plastic: "Plastic",
  paper: "Paper",
  metal: "Metal",
  glass: "Glass",
  e_waste: "E-Waste",
  organic: "Organic",
  other: "Other",
};

export const MATERIAL_COLORS: Record<keyof MaterialBreakdown, string> = {
  plastic: "#0ea5e9",
  paper: "#8b5cf6",
  metal: "#64748b",
  glass: "#14b8a6",
  e_waste: "#f59e0b",
  organic: "#22c55e",
  other: "#a1a1aa",
};

export interface MaterialBreakdownEntry {
  key: keyof MaterialBreakdown;
  label: string;
  value: number;
  color: string;
}

export function materialBreakdownEntries(
  breakdown: MaterialBreakdown,
): MaterialBreakdownEntry[] {
  return (Object.keys(MATERIAL_LABELS) as (keyof MaterialBreakdown)[])
    .map((key) => ({
      key,
      label: MATERIAL_LABELS[key],
      value: breakdown[key],
      color: MATERIAL_COLORS[key],
    }))
    .filter((entry) => entry.value > 0)
    .sort((left, right) => right.value - left.value);
}

export function formatAnalyticsNumber(
  value: number,
  maximumFractionDigits = 0,
): string {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits }).format(value);
}

export function formatPercent(value: number): string {
  return `${formatAnalyticsNumber(value, 1)}%`;
}

export function formatResponseTime(hours: number): string {
  if (!Number.isFinite(hours) || hours <= 0) {
    return "—";
  }
  return `${formatAnalyticsNumber(hours, 1)} h`;
}

export function formatMonthLabel(month: string): string {
  const [year, monthNumber] = month.split("-");
  const date = new Date(Number(year), Number(monthNumber) - 1, 1);
  return new Intl.DateTimeFormat(undefined, { month: "short" }).format(date);
}
