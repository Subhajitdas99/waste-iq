import { useQuery } from "@tanstack/react-query";
import {
  Bell,
  CircleAlert,
  Clock3,
  Lock,
  LogOut,
  Monitor,
  MoonStar,
  ShieldAlert,
  ShieldCheck,
  Sun,
} from "lucide-react";
import { getLoginHistory } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { NotificationCard } from "@/components/dashboard/NotificationCard";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { authQueryKeys } from "@/hooks/auth-query-keys";
import { REMEMBER_ME_KEY } from "@/lib/constants";
import { formatDateTime } from "@/lib/pickup";
import { getPortalConfig } from "@/lib/portal";
import type { LoginHistoryEntry } from "@/types/auth";

const LOGIN_HISTORY_PAGE = 1;
const LOGIN_HISTORY_PAGE_SIZE = 10;

const loginOutcomeCopy = {
  success: {
    label: "Successful login",
    className: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
    icon: ShieldCheck,
  },
  failure: {
    label: "Failed login",
    className: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-300",
    icon: ShieldAlert,
  },
} satisfies Record<
  LoginHistoryEntry["outcome"],
  {
    label: string;
    className: string;
    icon: typeof ShieldCheck;
  }
>;

function LoginHistoryLoadingState() {
  return (
    <div className="space-y-3" aria-label="Recent logins loading">
      {Array.from({ length: 3 }).map((_, index) => (
        <div key={index} className="rounded-2xl border bg-muted/20 p-4">
          <Skeleton className="h-4 w-36" />
          <Skeleton className="mt-3 h-3 w-48" />
          <Skeleton className="mt-3 h-3 w-full" />
        </div>
      ))}
    </div>
  );
}

function LoginHistoryEntryRow({ entry }: { entry: LoginHistoryEntry }) {
  const outcome = loginOutcomeCopy[entry.outcome];
  const OutcomeIcon = outcome.icon;
  const device = entry.user_agent ?? "Device information unavailable";
  const ipAddress = entry.ip_address ?? "IP address unavailable";

  return (
    <li className="rounded-2xl border bg-muted/20 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${outcome.className}`}
          >
            <OutcomeIcon className="h-3.5 w-3.5" aria-hidden="true" />
            {outcome.label}
          </span>
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock3 className="h-4 w-4 shrink-0" aria-hidden="true" />
            <time dateTime={entry.created_at}>{formatDateTime(entry.created_at)}</time>
          </p>
        </div>
        <p className="text-sm font-medium text-foreground sm:text-right">{ipAddress}</p>
      </div>
      <p
        className="mt-3 flex min-w-0 items-start gap-2 break-words text-sm text-muted-foreground"
        title={device}
      >
        <Monitor className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span>{device}</span>
      </p>
    </li>
  );
}

export function RoleSettingsPage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const loginHistoryQuery = useQuery({
    queryKey: authQueryKeys.loginHistory(LOGIN_HISTORY_PAGE, LOGIN_HISTORY_PAGE_SIZE),
    queryFn: () =>
      getLoginHistory({
        page: LOGIN_HISTORY_PAGE,
        page_size: LOGIN_HISTORY_PAGE_SIZE,
      }),
    meta: {
      suppressGlobalError: true,
    },
  });

  if (!user) {
    return null;
  }

  const portal = getPortalConfig(user.role);
  const loginHistoryItems = loginHistoryQuery.data?.items ?? [];
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
          title="Recent logins"
          description="Review recent sign-ins to your Waste-IQ account."
        >
          {loginHistoryQuery.isLoading ? (
            <LoginHistoryLoadingState />
          ) : loginHistoryQuery.isError ? (
            <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-4" role="alert">
              <div className="flex items-start gap-3">
                <CircleAlert className="mt-0.5 h-5 w-5 text-destructive" aria-hidden="true" />
                <div>
                  <p className="font-medium">Recent logins unavailable</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    We couldn't load your recent login activity. Please try again later.
                  </p>
                </div>
              </div>
            </div>
          ) : loginHistoryItems.length === 0 ? (
            <div className="rounded-2xl border border-dashed bg-muted/20 p-6 text-center">
              <p className="font-medium">No recent login activity.</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Successful and failed sign-in attempts will appear here.
              </p>
            </div>
          ) : (
            <ul className="space-y-3" aria-label="Recent login activity">
              {loginHistoryItems.map((entry) => (
                <LoginHistoryEntryRow key={entry.id} entry={entry} />
              ))}
            </ul>
          )}
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
