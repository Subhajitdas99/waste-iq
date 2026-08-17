import type { MonthlyStat } from "@/types/analytics";
import { AnalyticsChart, type AnalyticsChartDatum } from "./AnalyticsChart";
import { formatMonthLabel } from "@/lib/analytics";
import { cn } from "@/lib/utils";

interface MonthlyTrendChartProps {
  data: MonthlyStat[];
  className?: string;
}

export function MonthlyTrendChart({ data, className }: MonthlyTrendChartProps) {
  const chartData: AnalyticsChartDatum[] = data.map((entry) => ({
    label: formatMonthLabel(entry.month),
    value: entry.completed,
    secondaryValue: entry.pickup_count,
  }));

  return (
    <div className={cn("w-full", className)}>
      <div className="mb-3 flex items-center justify-end gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-emerald-500" />
          Completed
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-slate-300" />
          Total Pickups
        </span>
      </div>
      <AnalyticsChart
        data={chartData}
        emptyLabel="No pickup activity in the last 12 months."
        ariaLabel="Monthly pickup trend for the last 12 months"
      />
    </div>
  );
}
