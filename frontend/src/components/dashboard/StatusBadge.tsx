import { pickupStatusConfig, formatPickupStatus } from "@/lib/pickup";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config =
    pickupStatusConfig[status as keyof typeof pickupStatusConfig] ??
    pickupStatusConfig.pending;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em]",
        config.badgeClassName,
        className,
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", config.dotClassName)} aria-hidden="true" />
      {formatPickupStatus(status)}
    </span>
  );
}
