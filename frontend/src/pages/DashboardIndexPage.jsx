import AdminDashboard from "./admin/AdminDashboard";
import CitizenDashboard from "./citizen/CitizenDashboard";
import CollectorDashboard from "./collector/CollectorDashboard";
import { useAuth } from "../hooks/useAuth";

export default function DashboardIndexPage() {
  const { user } = useAuth();

  if (user?.role === "collector") {
    return <CollectorDashboard />;
  }

  if (user?.role === "admin") {
    return <AdminDashboard />;
  }

  return <CitizenDashboard />;
}
