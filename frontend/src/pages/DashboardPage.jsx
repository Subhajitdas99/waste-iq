import AppShell from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";
import AdminDashboard from "./admin/AdminDashboard";
import CitizenDashboard from "./citizen/CitizenDashboard";
import CollectorDashboard from "./collector/CollectorDashboard";

export default function DashboardPage() {
  const { user } = useAuth();

  const dashboards = {
    citizen: {
      title: "Pickup Request Tracker",
      subtitle: "Create recyclable waste pickups and follow each request until collection.",
      component: <CitizenDashboard />
    },
    collector: {
      title: "Lead Queue & Collections",
      subtitle: "Accept available jobs, track assignments, and close completed pickups with weight details.",
      component: <CollectorDashboard />
    },
    admin: {
      title: "Marketplace Analytics",
      subtitle: "See platform activity across users, requests, and collected recyclable weight.",
      component: <AdminDashboard />
    }
  };

  const config = dashboards[user?.role] || dashboards.citizen;

  return (
    <AppShell title={config.title} subtitle={config.subtitle}>
      {config.component}
    </AppShell>
  );
}
