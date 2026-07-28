import {
  UserCircle2,
  Mail,
  ShieldCheck,
  LogOut,
  Truck,
  CheckCircle2,
  Award,
} from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { ProfileCard } from "@/components/dashboard/ProfileCard";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { useCollectorSummary } from "@/hooks/useCollector";
import { formatDateTime } from "@/lib/pickup";

export function CollectorProfilePage() {
  const { user, logout } = useAuth();
  const summaryQuery = useCollectorSummary();

  const summary = summaryQuery.data;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <SeoHead
        title="Collector Profile"
        description="View collector account details, activity statistics, and manage session."
        path="/collector/profile"
      />

      <PageHeader
        title="Collector Profile"
        description="Collector account management and performance analytics."
      />

      {/* Collector Profile Hero Card */}
      <div className="relative overflow-hidden rounded-3xl border border-emerald-500/20 bg-gradient-to-r from-emerald-500/10 via-card to-card p-6 md:p-8 shadow-lg">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="relative">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-emerald-500 text-white shadow-lg shadow-emerald-500/30">
                <UserCircle2 className="h-12 w-12" />
              </div>
              <div className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-white ring-2 ring-background">
                <CheckCircle2 className="h-4 w-4" />
              </div>
            </div>

            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-bold tracking-tight text-foreground">
                  {user?.name ?? "Collector Account"}
                </h2>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Verified Collector
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
                <Mail className="h-4 w-4" />
                {user?.email ?? "collector@waste-iq.org"}
              </p>
            </div>
          </div>

          <Button
            type="button"
            variant="destructive"
            size="lg"
            className="gap-2.5 rounded-2xl shadow-md transition-all hover:scale-[1.02]"
            onClick={logout}
          >
            <LogOut className="h-5 w-5" />
            <span>Logout Account</span>
          </Button>
        </div>
      </div>

      {/* Profile Details & Collector Stats Grid */}
      <div className="grid gap-6 xl:grid-cols-2">
        {/* Account Information */}
        <div className="space-y-6">
          <ProfileCard
            title="Account Information"
            description="Personal details and credentials for your collector profile."
            items={[
              { label: "Full Name", value: user?.name ?? "Not available" },
              { label: "Email Address", value: user?.email ?? "Not available" },
              { label: "Phone Number", value: user?.phone ?? "Not provided" },
              { label: "Account Role", value: user?.role ? user.role.toUpperCase() : "COLLECTOR" },
              { label: "Member Since", value: formatDateTime(user?.created_at) },
              { label: "Collector ID", value: user ? `#COL-${user.id}` : "Not available" },
            ]}
          />

          <DashboardCard
            title="Collector Authorization"
            description="Operational access privileges and account verification state."
          >
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between rounded-xl border border-border/40 bg-muted/20 p-3.5">
                <div className="flex items-center gap-3">
                  <Truck className="h-5 w-5 text-emerald-500" />
                  <span className="font-medium">Waste Collection Vehicle Dispatch</span>
                </div>
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase bg-emerald-500/10 px-2.5 py-1 rounded-lg">
                  Authorized
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-border/40 bg-muted/20 p-3.5">
                <div className="flex items-center gap-3">
                  <Award className="h-5 w-5 text-emerald-500" />
                  <span className="font-medium">Recycling Center Access</span>
                </div>
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase bg-emerald-500/10 px-2.5 py-1 rounded-lg">
                  Active
                </span>
              </div>
            </div>
          </DashboardCard>
        </div>

        {/* Collector Performance Summary & Session Management */}
        <div className="space-y-6">
          <ProfileCard
            title="Collection Metrics"
            description="Real-time collection statistics loaded from collector summary service."
            items={[
              {
                label: "Total Assigned Jobs",
                value: summary ? String(summary.total_assigned) : summaryQuery.isLoading ? "Loading..." : "0",
              },
              {
                label: "Active In-Progress Jobs",
                value: summary ? String(summary.active_jobs) : summaryQuery.isLoading ? "Loading..." : "0",
              },
              {
                label: "Completed Jobs",
                value: summary ? String(summary.completed_jobs) : summaryQuery.isLoading ? "Loading..." : "0",
              },
              {
                label: "Total Weight Collected",
                value: summary ? `${summary.total_weight_kg.toFixed(1)} kg` : summaryQuery.isLoading ? "Loading..." : "0 kg",
              },
            ]}
          />

          <DashboardCard
            title="Account Session & Security"
            description="Manage your current session and securely sign out."
          >
            <div className="space-y-4">
              <div className="rounded-2xl border border-border/40 bg-card/60 p-4 text-sm text-muted-foreground">
                <p className="font-medium text-foreground flex items-center gap-2 mb-1">
                  <ShieldCheck className="h-4 w-4 text-emerald-500" /> Secure Collector Session
                </p>
                You are securely logged into the Waste-IQ Collector Portal. Clicking the logout button below will safely revoke session tokens from local storage.
              </div>

              <Button
                type="button"
                variant="destructive"
                className="w-full h-12 text-base font-semibold gap-2 rounded-xl shadow-md"
                onClick={logout}
              >
                <LogOut className="h-5 w-5" />
                <span>Logout Collector Session</span>
              </Button>
            </div>
          </DashboardCard>
        </div>
      </div>
    </div>
  );
}
