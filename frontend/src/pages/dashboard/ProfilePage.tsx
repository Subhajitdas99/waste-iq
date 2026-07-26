import { UserCircle2 } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { ProfileCard } from "@/components/dashboard/ProfileCard";
import { useAuth } from "@/context/AuthContext";
import { useCitizenPickupSummary } from "@/hooks/useCitizenPickups";
import { formatDateTime } from "@/lib/pickup";

export function ProfilePage() {
  const { user } = useAuth();
  const summaryQuery = useCitizenPickupSummary();

  return (
    <>
      <SeoHead
        title="Profile"
        description="View the current Waste-IQ citizen account details available from the backend."
        path="/dashboard/profile"
      />

      <PageHeader
        title="Profile"
        description="This page reflects the current `/auth/me` response and stays read-only because no citizen profile update endpoint exists yet."
      />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-6">
          <ProfileCard
            title="Account Details"
            description="Current user attributes loaded from the authentication API."
            items={[
              { label: "Full Name", value: user?.name ?? "Not available" },
              { label: "Email", value: user?.email ?? "Not available" },
              { label: "Phone", value: user?.phone ?? "Not available" },
              { label: "Role", value: user?.role ?? "Not available" },
              { label: "Member Since", value: formatDateTime(user?.created_at) },
              { label: "User ID", value: user ? String(user.id) : "Not available" },
            ]}
          />

          <DashboardCard
            title="Editing Constraints"
            description="The frontend avoids fake profile actions when the backend does not support them."
          >
            <div className="space-y-4 text-sm text-muted-foreground">
              <div className="rounded-2xl border bg-muted/20 p-4">
                Profile edits are not available because the current FastAPI backend only exposes
                `GET /auth/me` for citizen account data.
              </div>
              <div className="rounded-2xl border bg-muted/20 p-4">
                Change password is also unavailable because there is no password update endpoint in
                the current API contract.
              </div>
              <div className="rounded-2xl border bg-muted/20 p-4">
                Profile image upload is not implemented because the backend has no citizen profile
                picture endpoint.
              </div>
            </div>
          </DashboardCard>
        </div>

        <div className="space-y-6">
          <ProfileCard
            title="Citizen Activity"
            description="Pickup metrics coming from the citizen summary endpoint."
            items={[
              {
                label: "Total Requests",
                value: summaryQuery.data ? String(summaryQuery.data.total_requests) : "-",
              },
              {
                label: "Pending Requests",
                value: summaryQuery.data ? String(summaryQuery.data.pending_requests) : "-",
              },
              {
                label: "Accepted Requests",
                value: summaryQuery.data ? String(summaryQuery.data.accepted_requests) : "-",
              },
              {
                label: "Completed Requests",
                value: summaryQuery.data ? String(summaryQuery.data.completed_requests) : "-",
              },
            ]}
          />

          <DashboardCard
            title="Support"
            description="Need an account change that the current API cannot perform?"
          >
            <div className="rounded-2xl border bg-muted/20 p-5">
              <div className="flex items-start gap-3">
                <UserCircle2 className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Backend support required</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Sprint 3 keeps this experience honest: profile management stays view-only until
                    profile update endpoints are added to the FastAPI backend.
                  </p>
                </div>
              </div>
            </div>
          </DashboardCard>
        </div>
      </div>
    </>
  );
}
