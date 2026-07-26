import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Bell,
  ClipboardList,
  History,
  LayoutDashboard,
  Leaf,
  LogOut,
  Menu,
  Moon,
  Settings,
  Sun,
  UserCircle2,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const dashboardNavigation = [
  { label: "Overview", to: "/dashboard/overview", icon: LayoutDashboard },
  { label: "Pickups", to: "/dashboard/pickups", icon: ClipboardList },
  { label: "History", to: "/dashboard/history", icon: History },
  { label: "Profile", to: "/dashboard/profile", icon: UserCircle2 },
  { label: "Settings", to: "/dashboard/settings", icon: Settings },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-3 border-b px-5">
        <div className="rounded-2xl bg-primary/10 p-2 text-primary">
          <Leaf className="h-5 w-5" />
        </div>
        <div>
          <p className="font-semibold">Waste-IQ</p>
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
            Citizen Portal
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-2 p-4" aria-label="Dashboard navigation">
        {dashboardNavigation.map((item) => {
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

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  const currentLabel =
    dashboardNavigation.find((item) => location.pathname.startsWith(item.to))?.label ??
    "Dashboard";

  return (
    <div className="min-h-screen bg-background">
      <div className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-white/20 bg-card/80 backdrop-blur md:block">
        <SidebarContent />
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
            <SidebarContent onNavigate={() => setIsMobileMenuOpen(false)} />
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
                  Citizen Portal
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

              <div className="hidden rounded-full border bg-card/70 px-3 py-2 text-sm md:flex md:items-center md:gap-2">
                <Bell className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Notifications unavailable</span>
              </div>

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
          <Outlet />
        </main>
      </div>
    </div>
  );
}
