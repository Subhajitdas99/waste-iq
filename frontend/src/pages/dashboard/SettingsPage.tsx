import { Bell, Lock, LogOut, MoonStar, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { NotificationCard } from "@/components/dashboard/NotificationCard";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { REMEMBER_ME_KEY } from "@/lib/constants";

export function SettingsPage() {
  const { logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const rememberPreference =
    typeof window !== "undefined" && localStorage.getItem(REMEMBER_ME_KEY) === "true"
      ? "Remembered on this device"
      : "Session-only login";

  return (
    <>
      <SeoHead
        title="Settings"
        description="Adjust citizen portal theme preferences and review session behavior in Waste-IQ."
        path="/dashboard/settings"
      />

      <PageHeader
        title="Settings"
        description="Theme and session preferences can be managed here, while unsupported backend settings remain clearly marked."
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
                Bright surfaces with emerald and cyan highlights.
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
                Dark surfaces with the same established portal contrast palette.
              </p>
            </button>
          </div>
        </DashboardCard>

        <DashboardCard
          title="Session"
          description="Session behavior uses the existing authentication storage keys."
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
          description="Reusable UI is present, but there are no citizen notification endpoints in the backend."
        >
          <div className="space-y-4">
            <NotificationCard
              title="Notifications not connected"
              message="Unread counts, notification lists, and mark-as-read actions will be enabled once FastAPI notification endpoints exist."
              timestamp="Backend endpoint unavailable"
            />
            <div className="rounded-2xl border bg-muted/20 p-4 text-sm text-muted-foreground">
              The current Sprint 3 build intentionally avoids fake notifications or mock unread counts.
            </div>
          </div>
        </DashboardCard>

        <DashboardCard
          title="Security"
          description="Only supported settings are interactive. Unsupported security actions stay informational."
        >
          <div className="space-y-4">
            <div className="rounded-2xl border bg-muted/20 p-4">
              <div className="flex items-start gap-3">
                <Lock className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Password management unavailable</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    There is no citizen password update endpoint in the current FastAPI backend, so this settings page does not present a fake change-password form.
                  </p>
                </div>
              </div>
            </div>
            <div className="rounded-2xl border bg-muted/20 p-4">
              <div className="flex items-start gap-3">
                <Bell className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">Notification preferences unavailable</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Notification preference toggles will make sense once backend notification delivery exists.
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
