import { useState } from "react";
import { Edit3, Send } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { DealerApprovalBadge } from "@/components/dashboard/DealerApprovalBadge";
import { DealerApprovalTimeline } from "@/components/dashboard/DealerApprovalTimeline";
import { DealerProfileForm } from "@/components/dashboard/DealerProfileForm";
import { Button } from "@/components/ui/button";
import {
  useDealerProfile,
  useDealerProfileTimeline,
  useSubmitDealerProfile,
} from "@/hooks/useDealerProfile";
import { getApiErrorMessage, isNotFoundError } from "@/lib/api-error";

export function DealerProfilePage() {
  const [showForm, setShowForm] = useState(false);
  const profileQuery = useDealerProfile();
  const timelineQuery = useDealerProfileTimeline();
  const submitMutation = useSubmitDealerProfile();

  const profile = profileQuery.data;
  const hasNoProfile = profileQuery.isError && isNotFoundError(profileQuery.error);
  const canSubmit = Boolean(profile && ["draft", "rejected"].includes(profile.approval_status));

  if (profileQuery.isPending && !profile) {
    return (
      <>
        <SeoHead
          title="Dealer Profile"
          description="Manage your Waste-IQ dealer business profile and approval status."
          path="/dealer/profile"
        />
        <LoadingSkeleton count={2} />
      </>
    );
  }

  return (
    <>
      <SeoHead
        title="Dealer Profile"
        description="Manage your Waste-IQ dealer business profile and approval status."
        path="/dealer/profile"
      />

      <PageHeader
        title="Dealer Profile"
        description="Manage your business details and track your profile approval status."
      />

      {profileQuery.isError && !hasNoProfile ? (
        <div
          role="alert"
          className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
        >
          {getApiErrorMessage(profileQuery.error, "Unable to load your dealer profile.")}
        </div>
      ) : null}

      {hasNoProfile || !profile ? (
        <DashboardCard
          title="Create your dealer profile"
          description="Fill in your business details to start the approval process. A profile must be approved before you can browse or manage inventory."
        >
          <DealerProfileForm />
        </DashboardCard>
      ) : (
        <>
          <section className="rounded-3xl border bg-muted/20 p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h2 className="text-xl font-semibold tracking-tight">
                    {profile.business_name}
                  </h2>
                  <DealerApprovalBadge status={profile.approval_status} />
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {profile.owner_name} - {profile.profile_completion}% profile complete
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {canSubmit ? (
                  <Button
                    type="button"
                    className="gap-2"
                    disabled={submitMutation.isPending}
                    onClick={() => {
                      submitMutation.mutate();
                    }}
                  >
                    <Send className="h-4 w-4" />
                    {submitMutation.isPending ? "Submitting..." : "Submit for approval"}
                  </Button>
                ) : null}
                <Button
                  type="button"
                  variant="outline"
                  className="gap-2"
                  onClick={() => setShowForm((current) => !current)}
                >
                  <Edit3 className="h-4 w-4" />
                  {showForm ? "Hide form" : "Edit profile"}
                </Button>
              </div>
            </div>

            {profile.approval_status === "approved" ? (
              <p className="mt-4 text-sm text-emerald-700 dark:text-emerald-300">
                Your profile is approved. You can browse the inventory marketplace
                and manage your inventory.
              </p>
            ) : profile.approval_status === "rejected" ? (
              <div className="mt-4 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                <p className="font-semibold">Your application was rejected</p>
                <p className="mt-1">
                  {profile.rejection_reason ??
                    "No rejection reason was provided. Please edit your profile and submit it again."}
                </p>
              </div>
            ) : profile.approval_status === "submitted" ? (
              <p className="mt-4 text-sm text-muted-foreground">
                Your profile is awaiting review by an administrator. You will be
                able to browse inventory once it is approved.
              </p>
            ) : (
              <p className="mt-4 text-sm text-muted-foreground">
                Your profile is saved as a draft. Submit it for review to unlock
                inventory access.
              </p>
            )}
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-2">
            <DashboardCard title="Business details" description="Information stored on your dealer profile.">
              <dl className="grid gap-4 sm:grid-cols-2">
                {[
                  ["Phone", profile.phone],
                  ["Email", profile.email ?? "Not provided"],
                  ["Address", profile.address],
                  ["City", profile.city],
                  ["State", profile.state ?? "Not provided"],
                  ["Postal code", profile.postal_code],
                  ["GST number", profile.gst_number ?? "Not provided"],
                  ["License number", profile.license_number ?? "Not provided"],
                  ["Business type", profile.business_type ?? "Not provided"],
                  [
                    "Accepted materials",
                    profile.materials_accepted.join(", ") || "Not provided",
                  ],
                ].map(([label, value]) => (
                  <div key={label}>
                    <dt className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                      {label}
                    </dt>
                    <dd className="mt-1 text-sm font-medium">{value}</dd>
                  </div>
                ))}
              </dl>
              <div className="mt-4">
                <dt className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                  Description
                </dt>
                <dd className="mt-1 text-sm text-muted-foreground">
                  {profile.description ?? "No description provided."}
                </dd>
              </div>
            </DashboardCard>

            <DashboardCard
              title="Approval timeline"
              description="Every status change recorded against your profile."
            >
              {timelineQuery.isPending ? (
                <LoadingSkeleton count={2} />
              ) : timelineQuery.isError ? (
                <div role="alert" className="text-sm text-destructive">
                  {getApiErrorMessage(
                    timelineQuery.error,
                    "Unable to load the approval timeline.",
                  )}
                </div>
              ) : (
                <DealerApprovalTimeline events={timelineQuery.data ?? []} />
              )}
            </DashboardCard>
          </section>

          {showForm ? (
            <section className="mt-6">
              <DashboardCard
                title="Edit profile"
                description="Changes reset your approval status to draft for re-review."
              >
                <DealerProfileForm profile={profile} />
              </DashboardCard>
            </section>
          ) : null}
        </>
      )}
    </>
  );
}
