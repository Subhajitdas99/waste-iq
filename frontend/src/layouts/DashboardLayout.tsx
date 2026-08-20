import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Leaf,
  LogOut,
  Mail,
  Menu,
  Moon,
  ShieldAlert,
  Sun,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { Button } from "@/components/ui/button";
import { NotificationDropdown } from "@/components/dashboard/notifications/NotificationDropdown";
import { getPortalConfig } from "@/lib/portal";
import { cn } from "@/lib/utils";
import { authQueryKeys } from "@/hooks/auth-query-keys";
import { resendVerification } from "@/api/auth";
import { getRateLimitRetryAfterSeconds, isRateLimitError } from "@/lib/api-error";

function SidebarContent({
  portalName,
  navigation,
  onNavigate,
}: {
  portalName: string;
  navigation: ReturnType<typeof getPortalConfig>["navigation"];
  onNavigate?: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-3 border-b px-5">
        <div className="rounded-2xl bg-primary/10 p-2 text-primary">
          <Leaf className="h-5 w-5" />
        </div>
        <div>
          <p className="font-semibold">Waste-IQ</p>
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
            {portalName}
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-2 p-4" aria-label="Dashboard navigation">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}

function VerificationBanner() {
  const { user } = useAuth();
  const { data: profile } = useQuery({
    queryKey: authQueryKeys.currentUser,
    staleTime: 60_000,
  });
  const [notice, setNotice] = useState<string | null>(null);

  const emailVerified = profile?.email_verified ?? user?.email_verified ?? true;

  const resendMutation = useMutation({
    meta: {
      suppressGlobalError: true,
    },
    mutationFn: resendVerification,
    onSuccess: (response) => {
      setNotice(response.message);
    },
  });

  if (emailVerified || !user) {
    return null;
  }

  const onResend = async () => {
    setNotice(null);
    try {
      await resendMutation.mutateAsync(user.email);
    } catch (error) {
      if (isRateLimitError(error)) {
        const seconds = getRateLimitRetryAfterSeconds(error);
        const minutes = seconds !== null ? Math.max(1, Math.ceil(seconds / 60)) : null;
        setNotice(
          minutes !== null
            ? `Too many attempts. Please try again in about ${minutes} minute${minutes === 1 ? "" : "s"}.`
            : "Too many attempts. Please try again later."
        );
        return;
      }
      setNotice("Unable to resend the verification email.");
    }
  };

  return (
    <div
      role="status"
      className="flex flex-wrap items-center gap-3 border border-primary/30 bg-primary/10 px-4 py-3 text-sm rounded-lg mb-6"
    >
      <ShieldAlert className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
      <p className="flex-1 min-w-40">
        Your email address is not verified yet.{" "}
        {notice && <span className="block font-medium text-primary">{notice}</span>}
      </p>
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="gap-2"
        onClick={onResend}
        disabled={resendMutation.isPending}
      >
        {resendMutation.isPending ? (
          <span className="flex items-center gap-2">Sending...</span>
        ) : (
          <>
            <Mail className="h-4 w-4" aria-hidden="true" />
            Resend verification email
          </>
        )}
      </Button>
    </div>
  );
}

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const portal = getPortalConfig(user?.role ?? "citizen");

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  const currentLabel =
    portal.navigation.find((item) => location.pathname.startsWith(item.to))?.label ??
    "Dashboard";

  return (
    <div className="min-h-screen bg-background">
      <div className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-white/20 bg-card/80 backdrop-blur md:block">
        <SidebarContent portalName={portal.portalName} navigation={portal.navigation} />
      </div>

      {isMobileMenuOpen ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-background/70 backdrop-blur-sm"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-label="Close navigation"
          />
          <aside className="relative z-10 h-full w-72 border-r bg-card shadow-xl">
            <SidebarContent
              portalName={portal.portalName}
              navigation={portal.navigation}
              onNavigate={() => setIsMobileMenuOpen(false)}
            />
          </aside>
        </div>
      ) : null}

      <div className="md:pl-72">
        <header className="sticky top-0 z-20 border-b border-white/20 bg-background/80 backdrop-blur">
          <div className="flex min-h-16 items-center justify-between gap-4 px-4 py-3 lg:px-8">
            <div className="flex items-center gap-3">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => setIsMobileMenuOpen(true)}
                aria-label="Open dashboard navigation"
              >
                <Menu className="h-5 w-5" />
              </Button>
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">
                  {portal.portalName}
                </p>
                <h1 className="text-lg font-semibold">{currentLabel}</h1>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              >
                {theme === "dark" ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </Button>

              <NotificationDropdown
                notificationsPath={`${getPortalConfig(user?.role ?? "citizen").routePrefix}/notifications`}
              />

              <div className="hidden rounded-full border bg-card/70 px-4 py-2 text-sm md:block">
                <span className="font-medium">{user?.name ?? user?.email}</span>
                <span className="ml-2 capitalize text-muted-foreground">{user?.role}</span>
              </div>

              <Button type="button" variant="outline" className="gap-2" onClick={logout}>
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </header>

        <main className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-background via-background to-primary/5 px-4 py-6 lg:px-8 lg:py-8">
          <VerificationBanner />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
