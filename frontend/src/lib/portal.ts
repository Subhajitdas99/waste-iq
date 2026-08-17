import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  Bell,
  ClipboardList,
  History,
  LayoutDashboard,
  Map,
  Settings,
  ShoppingCart,
  Store,
  UserCircle2,
} from "lucide-react";
import type { UserRole } from "@/types/auth";

export interface PortalNavigationItem {
  label: string;
  to: string;
  icon: LucideIcon;
}

export interface PortalConfig {
  role: UserRole;
  portalName: string;
  portalTagline: string;
  homePath: string;
  routePrefix: string;
  navigation: PortalNavigationItem[];
}

export const portalConfigByRole: Record<UserRole, PortalConfig> = {
  citizen: {
    role: "citizen",
    portalName: "Citizen Portal",
    portalTagline: "Schedule pickups and track recyclable waste collections.",
    homePath: "/dashboard/overview",
    routePrefix: "/dashboard",
    navigation: [
      { label: "Overview", to: "/dashboard/overview", icon: LayoutDashboard },
      { label: "Pickups", to: "/dashboard/pickups", icon: ClipboardList },
      { label: "History", to: "/dashboard/history", icon: History },
      { label: "Notifications", to: "/dashboard/notifications", icon: Bell },
      { label: "Profile", to: "/dashboard/profile", icon: UserCircle2 },
      { label: "Settings", to: "/dashboard/settings", icon: Settings },
    ],
  },
  collector: {
    role: "collector",
    portalName: "Collector Portal",
    portalTagline: "Review assignments, accept new jobs, and complete collection runs.",
    homePath: "/collector/overview",
    routePrefix: "/collector",
    navigation: [
      { label: "Overview", to: "/collector/overview", icon: LayoutDashboard },
      { label: "Live Map", to: "/collector/map", icon: Map },
      { label: "Notifications", to: "/collector/notifications", icon: Bell },
      { label: "Profile", to: "/collector/profile", icon: UserCircle2 },
      { label: "Settings", to: "/collector/settings", icon: Settings },
    ],
  },
  dealer: {
    role: "dealer",
    portalName: "Dealer Portal",
    portalTagline: "Manage dealer onboarding and browse recyclable inventory lots.",
    homePath: "/dealer/overview",
    routePrefix: "/dealer",
    navigation: [
      { label: "Overview", to: "/dealer/overview", icon: LayoutDashboard },
      { label: "Inventory", to: "/dealer/inventory", icon: ClipboardList },
      { label: "Marketplace", to: "/dealer/marketplace", icon: Store },
      { label: "Orders & History", to: "/dealer/orders", icon: ShoppingCart },
      { label: "Notifications", to: "/dealer/notifications", icon: Bell },
      { label: "Profile", to: "/dealer/profile", icon: UserCircle2 },
      { label: "Settings", to: "/dealer/settings", icon: Settings },
    ],
  },
  admin: {
    role: "admin",
    portalName: "Admin Portal",
    portalTagline: "Oversee users, dealers, analytics, and inventory governance.",
    homePath: "/admin/overview",
    routePrefix: "/admin",
    navigation: [
      { label: "Overview", to: "/admin/overview", icon: LayoutDashboard },
      { label: "AI Analytics", to: "/admin/analytics", icon: BarChart3 },
      { label: "Notifications", to: "/admin/notifications", icon: Bell },
      { label: "Profile", to: "/admin/profile", icon: UserCircle2 },
      { label: "Settings", to: "/admin/settings", icon: Settings },
    ],
  },
};

export function getPortalConfig(role: UserRole): PortalConfig {
  return portalConfigByRole[role];
}

export function getRoleHomePath(role?: UserRole | null): string {
  if (!role) {
    return "/login";
  }

  return portalConfigByRole[role].homePath;
}

export function getRolePortalLabel(role?: UserRole | null): string {
  if (!role) {
    return "Waste-IQ Portal";
  }

  return portalConfigByRole[role].portalName;
}

export function canRoleAccessPath(role: UserRole, path?: string | null): boolean {
  if (!path) {
    return false;
  }

  return path === portalConfigByRole[role].routePrefix ||
    path.startsWith(`${portalConfigByRole[role].routePrefix}/`);
}

export function resolvePostLoginPath(role: UserRole, requestedPath?: string | null): string {
  if (canRoleAccessPath(role, requestedPath)) {
    return requestedPath as string;
  }

  return getRoleHomePath(role);
}
