import { lazy, Suspense } from "react";

import { useAuth } from "../hooks/useAuth";

const AdminDashboard = lazy(() => import("./admin/AdminDashboard"));
const CitizenDashboard = lazy(() => import("./citizen/CitizenDashboard"));
const CollectorDashboard = lazy(() => import("./collector/CollectorDashboard"));
const DealerDashboard = lazy(() => import("./dealer/DealerDashboard"));

function DashboardFallback() {
  return <p className="text-sm text-ink/70">Loading dashboard...</p>;
}

export default function DashboardIndexPage() {
  const { user } = useAuth();
  let dashboard = <CitizenDashboard />;

  if (user?.role === "collector") {
    dashboard = <CollectorDashboard />;
  } else if (user?.role === "admin") {
    dashboard = <AdminDashboard />;
  } else if (user?.role === "dealer") {
    dashboard = <DealerDashboard />;
  }

  return <Suspense fallback={<DashboardFallback />}>{dashboard}</Suspense>;
}
