import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { LoadingScreen } from "@/components/ui/spinner";

interface GuestRouteProps {
  children: ReactNode;
}

export function GuestRoute({ children }: GuestRouteProps) {
  const { user, token, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (token && user) {
    if (user.role === "collector") {
      return <Navigate to="/collector/profile" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
