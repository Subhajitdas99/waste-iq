import { Bell, Lock, LogOut, MoonStar, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { NotificationCard } from "@/components/dashboard/NotificationCard";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { REMEMBER_ME_KEY } from "@/lib/constants";
import { getPortalConfig } from "@/lib/portal";

export function RoleSettingsPage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();

  if (!user) {
    return null;
  }

  const portal = getPortalConfig(user.role);
  const rememberPreference =
    typeof window !== "undefined" && localStorage.getItem(REMEMBER_ME_KEY) === "true"
      ? "Remembered on this device"
      : "Session-only login";

  return (
    <>
      <SeoHead
        title={`${portal.portalName} Settings`}
        description={`Manage theme and session preferences for the ${user.role} portal in Waste-IQ.`}
        path={`${portal.homePath.replace("/overview", "")}/settings`}
      />

      <PageHeader
        title="Settings"
        description={`Theme and session controls are active for the ${portal.portalName.toLowerCase()}, while unsupported account-management actions stay clearly informational.`}
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <DashboardCard
          title="Appearance"
          description="Theme selection is a real frontend preference stored in the browser."
        >
          <div className="grid gap-3 md:grid-cols-2">
            <button
              type="button"
              onClick={() => setTheme("light")}
              className={`rounded-2xl border p-5 text-left transition ${
                theme === "light" ? "border-primary bg-primary/10" : "bg-muted/20"
              }`}
            >
              <Sun className="h-5 w-5 text-primary" />
              <p className="mt-4 font-medium">Light mode</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Bright surfaces with the established Waste-IQ accent palette.
              </p>
            </button>
            <button
              type="button"
              onClick={() => setTheme("dark")}
              className={`rounded-2xl border p-5 text-left transition ${
                theme === "dark" ? "border-primary bg-primary/10" : "bg-muted/20"
              }`}
            >
              <MoonStar className="h-5 w-5 text-primary" />
              <p className="mt-4 font-medium">Dark mode</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Dark surfaces that preserve the same portal contrast language.
              </p>
            </button>
          </div>
        </DashboardCard>

        <DashboardCard
          title="Session"
          description="Session behavior uses the shared authentication storage flow."
        >
          <div className="space-y-4">
            <div className="rounded-2xl border bg-muted/20 p-4">
              <p className="text-sm font-medium">Remember me preference</p>
              <p className="mt-2 text-sm text-muted-foreground">{rememberPreference}</p>
            </div>
            <Button variant="outline" className="gap-2" onClick={logout}>
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          </div>
        </DashboardCard>

        <DashboardCard
          title="Notifications"
          description="Notification delivery remains backend-dependent for every authenticated role."
        >
          <div className="space-y-4">
            <NotificationCard
              title="Notifications not connected"
              message={`The ${portal.portalName.toLowerCase()} does not yet have dedicated notification endpoints wired into the frontend.`}
              timestamp="Backend endpoint unavailable"
            />
            <div className="rounded-2xl border bg-muted/20 p-4 text-sm text-muted-foreground">
              Route protection is now complete, and notification preferences can be layered into this
              settings surface once role-specific delivery APIs are connected.
            </div>
          </div>
        </DashboardCard>

        <DashboardCard
          title="Security"
          description="Unsupported security actions remain informational until backed by real endpoints."
        >
          <div className="space-y-4">
            <div className="rounded-2xl border bg-muted/20 p-4">
              <div className="flex items-start gap-3">
                <Lock className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Password management unavailable</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    There is no role-specific password update flow connected in the current frontend,
                    so this portal intentionally avoids showing a fake security form.
                  </p>
                </div>
              </div>
            </div>
            <div className="rounded-2xl border bg-muted/20 p-4">
              <div className="flex items-start gap-3">
                <Bell className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Preference delivery pending integration</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Notification preference toggles can be connected cleanly later without changing
                    this role-specific settings layout.
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
