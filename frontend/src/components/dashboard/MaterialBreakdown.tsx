import type { MaterialBreakdown } from "@/types/analytics";
import {
  formatAnalyticsNumber,
  formatPercent,
  materialBreakdownEntries,
} from "@/lib/analytics";
import { cn } from "@/lib/utils";

interface MaterialBreakdownProps {
  data: MaterialBreakdown | null;
  className?: string;
}

export function MaterialBreakdown({ data, className }: MaterialBreakdownProps) {
  const entries = data ? materialBreakdownEntries(data) : [];
  const total = entries.reduce((sum, entry) => sum + entry.value, 0);

  if (!data || total === 0) {
    return (
      <div className="rounded-2xl border border-dashed bg-muted/20 px-4 py-8 text-center text-sm text-muted-foreground">
        Material distribution appears once completed pickups are categorized.
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {entries.map((entry) => (
        <div key={entry.key}>
          <div className="mb-1.5 flex items-center justify-between text-sm">
            <span className="font-medium">{entry.label}</span>
            <span className="text-muted-foreground">
              {formatAnalyticsNumber(entry.value)} ·{" "}
              {formatPercent((entry.value / total) * 100)}
            </span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-muted/40">
            <div
              className="h-full rounded-full"
              style={{
                width: `${(entry.value / total) * 100}%`,
                backgroundColor: entry.color,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
