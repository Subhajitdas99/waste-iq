import { ShieldCheck, UserCircle2 } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { ProfileCard } from "@/components/dashboard/ProfileCard";
import { useAuth } from "@/context/AuthContext";
import { formatDateTime } from "@/lib/pickup";
import { getPortalConfig } from "@/lib/portal";

export function RoleProfilePage() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  const portal = getPortalConfig(user.role);

  return (
    <>
      <SeoHead
        title={`${portal.portalName} Profile`}
        description={`Review authenticated ${user.role} account details in Waste-IQ.`}
        path={`${portal.homePath.replace("/overview", "")}/profile`}
      />

      <PageHeader
        title="Profile"
        description={`This read-only account view reflects the current authenticated ${user.role} record returned by \`/auth/me\`.`}
      />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <ProfileCard
          title="Account Details"
          description="Current user attributes loaded from the authentication API."
          items={[
            { label: "Full Name", value: user.name },
            { label: "Email", value: user.email },
            { label: "Phone", value: user.phone },
            { label: "Role", value: user.role },
            { label: "Member Since", value: formatDateTime(user.created_at) },
            { label: "User ID", value: String(user.id) },
          ]}
        />

        <DashboardCard
          title="Current Access"
          description="Role-aware routing is now enforced from the frontend and backend."
        >
          <div className="space-y-4 text-sm text-muted-foreground">
            <div className="rounded-2xl border bg-muted/20 p-4">
              <div className="flex items-start gap-3">
                <UserCircle2 className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium text-foreground">{portal.portalName}</p>
                  <p className="mt-2">{portal.portalTagline}</p>
                </div>
              </div>
            </div>
            <div className="rounded-2xl border bg-muted/20 p-4">
              <div className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium text-foreground">Read-only profile view</p>
                  <p className="mt-2">
                    Profile editing stays intentionally limited until the corresponding backend
                    endpoints are connected for this role.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </DashboardCard>
      </div>
    </>
  );
}
