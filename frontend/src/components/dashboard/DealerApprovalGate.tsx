import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { FileWarning, ShieldAlert, UserRoundCog } from "lucide-react";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import { useDealerProfile } from "@/hooks/useDealerProfile";
import { getApiErrorMessage, isNotFoundError } from "@/lib/api-error";
import { formatDealerApprovalStatus } from "@/lib/dealerApproval";

interface DealerApprovalGateProps {
  children: ReactNode;
}

export function DealerApprovalGate({ children }: DealerApprovalGateProps) {
  const profileQuery = useDealerProfile();
  const profile = profileQuery.data;

  if (profileQuery.isPending && !profile) {
    return <LoadingSkeleton count={2} />;
  }

  if (profileQuery.isError) {
    if (isNotFoundError(profileQuery.error)) {
      return (
        <div className="rounded-3xl border bg-muted/20 p-8 text-center">
          <FileWarning className="mx-auto h-10 w-10 text-muted-foreground" aria-hidden="true" />
          <h2 className="mt-4 text-xl font-semibold tracking-tight">
            Dealer profile required
          </h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
            You must create and submit a dealer profile before you can access the
            inventory marketplace.
          </p>
          <Button asChild className="mt-6">
            <Link to="/dealer/profile">Set up your dealer profile</Link>
          </Button>
        </div>
      );
    }

    return (
      <div
        role="alert"
        className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
      >
        {getApiErrorMessage(profileQuery.error, "Unable to load your dealer profile.")}
      </div>
    );
  }

  if (!profile || profile.approval_status !== "approved") {
    const statusLabel = profile
      ? formatDealerApprovalStatus(profile.approval_status)
      : "not submitted";
    const Icon = profile ? ShieldAlert : UserRoundCog;

    return (
      <div className="rounded-3xl border bg-muted/20 p-8 text-center">
        <Icon className="mx-auto h-10 w-10 text-muted-foreground" aria-hidden="true" />
        <h2 className="mt-4 text-xl font-semibold tracking-tight">Approval required</h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
          Your dealer profile is currently{" "}
          <span className="font-semibold capitalize">{statusLabel}</span>. Inventory
          browsing is available once an administrator approves your profile.
        </p>
        <Button asChild className="mt-6">
          <Link to="/dealer/profile">View my dealer profile</Link>
        </Button>
      </div>
    );
  }

  return <>{children}</>;
}
