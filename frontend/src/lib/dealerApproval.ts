import type { DealerApprovalStatus } from "@/types/dealer";

export const dealerApprovalStatusConfig: Record<
  DealerApprovalStatus,
  { label: string; badgeClassName: string; dotClassName: string }
> = {
  draft: {
    label: "Draft",
    badgeClassName:
      "border-slate-500/20 bg-slate-500/10 text-slate-700 dark:text-slate-300",
    dotClassName: "bg-slate-500",
  },
  submitted: {
    label: "Pending Review",
    badgeClassName:
      "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300",
    dotClassName: "bg-amber-500",
  },
  approved: {
    label: "Approved",
    badgeClassName:
      "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
    dotClassName: "bg-emerald-500",
  },
  rejected: {
    label: "Rejected",
    badgeClassName:
      "border-destructive/20 bg-destructive/10 text-destructive",
    dotClassName: "bg-destructive",
  },
};

export function formatDealerApprovalStatus(status: string): string {
  if (status in dealerApprovalStatusConfig) {
    return dealerApprovalStatusConfig[status as DealerApprovalStatus].label;
  }

  return status.replace(/_/g, " ");
}

export function isDealerApproved(status: DealerApprovalStatus | undefined): boolean {
  return status === "approved";
}
