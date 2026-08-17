import {
  dealerApprovalStatusConfig,
  formatDealerApprovalStatus,
} from "@/lib/dealerApproval";
import { cn } from "@/lib/utils";

interface DealerApprovalBadgeProps {
  status: string;
  className?: string;
}

export function DealerApprovalBadge({ status, className }: DealerApprovalBadgeProps) {
  const config =
    dealerApprovalStatusConfig[
      status as keyof typeof dealerApprovalStatusConfig
    ] ?? dealerApprovalStatusConfig.draft;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em]",
        config.badgeClassName,
        className,
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", config.dotClassName)} aria-hidden="true" />
      {formatDealerApprovalStatus(status)}
    </span>
  );
}
