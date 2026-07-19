import { Outlet, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import AppShell from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";
import CitizenDashboardNav from "../components/citizen/CitizenDashboardNav";

const queryClient = new QueryClient();

export default function DashboardPage() {
  const { user } = useAuth();
  const location = useLocation();

  const dashboards = {
    citizen: {
      title: "Citizen Dashboard",
      subtitle: "Schedule pickups, track every status change, and stay in sync with assigned collectors."
    },
    collector: {
      title: "Lead Queue & Collections",
      subtitle: "Accept available jobs, track assignments, and close completed pickups with weight details."
    },
    dealer: {
      title: "Dealer Dashboard",
      subtitle: "Complete your business profile, track verification status, and wait for admin approval before dealer marketplace work begins."
    },
    admin: {
      title: "Marketplace Analytics",
      subtitle: "See platform activity across users, requests, and collected recyclable weight."
    }
  };

  const isCitizen = user?.role === "citizen";
  const config = dashboards[user?.role] || dashboards.citizen;

  const citizenRouteContent = {
    "/dashboard": {
      title: "Citizen Dashboard",
      subtitle: "A live command center for pickup activity, recent requests, and quick scheduling."
    },
    "/dashboard/requests": {
      title: "My Requests",
      subtitle: "Review every pickup request in table or card view, with direct access to details and cancellation."
    }
  };

  const detailConfig =
    isCitizen && location.pathname.startsWith("/dashboard/requests/")
      ? {
          title: "Request Details",
          subtitle: "See the complete pickup record, assigned collector, and the full status timeline."
        }
      : null;

  const citizenConfig = detailConfig || citizenRouteContent[location.pathname] || dashboards.citizen;
  const shellConfig = isCitizen ? citizenConfig : config;

  return (
    <QueryClientProvider client={queryClient}>
      <AppShell title={shellConfig.title} subtitle={shellConfig.subtitle}>
        {isCitizen ? <CitizenDashboardNav /> : null}
        <Outlet />
      </AppShell>
    </QueryClientProvider>
  );
}
