import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Leaf,
  LogOut,
  Menu,
  Moon,
  Sun,
  UserCircle2,
  ShieldCheck,
  Truck,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const collectorNavigation = [
  { label: "Profile", to: "/collector/profile", icon: UserCircle2 },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full flex-col justify-between p-4">
      <div>
        <div className="flex h-16 items-center gap-3 border-b border-border/40 px-2 pb-4">
          <div className="rounded-2xl bg-emerald-500/15 p-2 text-emerald-500 dark:bg-emerald-500/20">
            <Truck className="h-6 w-6" />
          </div>
          <div>
            <p className="font-bold tracking-tight text-foreground">Waste-IQ</p>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400">
              Collector Portal
            </p>
          </div>
        </div>

        <nav className="mt-6 space-y-2" aria-label="Collector dashboard navigation">
          {collectorNavigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )
                }
              >
                <Icon className="h-5 w-5" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="space-y-4 border-t border-border/40 pt-4">
        <div className="rounded-2xl border border-border/50 bg-card/60 p-3 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="truncate text-sm font-semibold text-foreground">
                {user?.name ?? user?.email ?? "Collector"}
              </p>
              <p className="text-xs capitalize text-emerald-600 dark:text-emerald-400 font-medium">
                {user?.role ?? "collector"}
              </p>
            </div>
          </div>
        </div>

        <Button
          type="button"
          variant="destructive"
          className="w-full gap-2 rounded-xl shadow-sm"
          onClick={logout}
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </Button>
      </div>
    </div>
  );
}

export function CollectorDashboardLayout() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Desktop Sidebar */}
      <div className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-border/40 bg-card/80 backdrop-blur-md md:block">
        <SidebarContent />
      </div>

      {/* Mobile Drawer */}
      {isMobileMenuOpen ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-background/70 backdrop-blur-sm"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-label="Close navigation"
          />
          <aside className="relative z-10 h-full w-72 border-r bg-card shadow-2xl">
            <SidebarContent onNavigate={() => setIsMobileMenuOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="md:pl-72">
        {/* Top Navbar */}
        <header className="sticky top-0 z-20 border-b border-border/40 bg-background/80 backdrop-blur-md">
          <div className="flex min-h-16 items-center justify-between gap-4 px-4 py-3 lg:px-8">
            <div className="flex items-center gap-3">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => setIsMobileMenuOpen(true)}
                aria-label="Open navigation"
              >
                <Menu className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-2">
                <div className="hidden sm:flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
                  <Leaf className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400">
                    Collector Workspace
                  </p>
                  <h1 className="text-lg font-bold tracking-tight">Collector Profile</h1>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
                className="rounded-xl"
              >
                {theme === "dark" ? (
                  <Sun className="h-5 w-5 text-amber-400" />
                ) : (
                  <Moon className="h-5 w-5 text-slate-700" />
                )}
              </Button>

              <div className="hidden rounded-xl border border-border/50 bg-card/70 px-3.5 py-1.5 text-sm font-medium md:flex md:items-center md:gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>{user?.name ?? user?.email}</span>
                <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-xs uppercase font-semibold text-emerald-600 dark:text-emerald-400">
                  {user?.role}
                </span>
              </div>

              <Button
                type="button"
                variant="destructive"
                size="sm"
                className="gap-2 rounded-xl"
                onClick={logout}
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-background via-background to-emerald-500/5 px-4 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
