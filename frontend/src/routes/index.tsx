import { lazy, Suspense, type ComponentType } from "react";
import { Navigate, createBrowserRouter } from "react-router-dom";
import { PublicLayout } from "../layouts/PublicLayout";
import { AuthLayout } from "../layouts/AuthLayout";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { ProtectedRoute } from "./ProtectedRoute";
import { GuestRoute } from "./GuestRoute";
import { LoadingScreen } from "@/components/ui/spinner";

const LandingPage = lazy(() =>
  import("../pages/public/LandingPage").then((m) => ({ default: m.LandingPage }))
);
const FeaturesPage = lazy(() =>
  import("../pages/public/FeaturesPage").then((m) => ({ default: m.FeaturesPage }))
);
const AboutPage = lazy(() =>
  import("../pages/public/AboutPage").then((m) => ({ default: m.AboutPage }))
);
const ContactPage = lazy(() =>
  import("../pages/public/ContactPage").then((m) => ({ default: m.ContactPage }))
);
const LoginPage = lazy(() =>
  import("../pages/auth/LoginPage").then((m) => ({ default: m.LoginPage }))
);
const RegisterPage = lazy(() =>
  import("../pages/auth/RegisterPage").then((m) => ({ default: m.RegisterPage }))
);
const NotFoundPage = lazy(() =>
  import("../pages/public/NotFoundPage").then((m) => ({ default: m.NotFoundPage }))
);
const UnauthorizedPage = lazy(() =>
  import("../pages/public/NotFoundPage").then((m) => ({ default: m.UnauthorizedPage }))
);
const DashboardOverviewPage = lazy(() =>
  import("../pages/dashboard/DashboardOverviewPage").then((m) => ({
    default: m.DashboardOverviewPage,
  }))
);
const CollectorOverviewPage = lazy(() =>
  import("../pages/dashboard/CollectorOverviewPage").then((m) => ({
    default: m.CollectorOverviewPage,
  }))
);
const CollectorPickupDetailsPage = lazy(() =>
  import("../pages/dashboard/CollectorPickupDetailsPage").then((m) => ({
    default: m.CollectorPickupDetailsPage,
  }))
);
const DealerOverviewPage = lazy(() =>
  import("../pages/dashboard/DealerOverviewPage").then((m) => ({
    default: m.DealerOverviewPage,
  }))
);
const AdminOverviewPage = lazy(() =>
  import("../pages/dashboard/AdminOverviewPage").then((m) => ({
    default: m.AdminOverviewPage,
  }))
);
const AIAnalyticsPage = lazy(() =>
  import("../pages/dashboard/AIAnalyticsPage").then((m) => ({
    default: m.AIAnalyticsPage,
  }))
);
const CitizenPickupsPage = lazy(() =>
  import("../pages/dashboard/CitizenPickupsPage").then((m) => ({
    default: m.CitizenPickupsPage,
  }))
);
const NewPickupPage = lazy(() =>
  import("../pages/dashboard/NewPickupPage").then((m) => ({
    default: m.NewPickupPage,
  }))
);
const PickupDetailsPage = lazy(() =>
  import("../pages/dashboard/PickupDetailsPage").then((m) => ({
    default: m.PickupDetailsPage,
  }))
);
const PickupHistoryPage = lazy(() =>
  import("../pages/dashboard/PickupHistoryPage").then((m) => ({
    default: m.PickupHistoryPage,
  }))
);
const ProfilePage = lazy(() =>
  import("../pages/dashboard/ProfilePage").then((m) => ({
    default: m.ProfilePage,
  }))
);
const RoleProfilePage = lazy(() =>
  import("../pages/dashboard/RoleProfilePage").then((m) => ({
    default: m.RoleProfilePage,
  }))
);
const RoleSettingsPage = lazy(() =>
  import("../pages/dashboard/RoleSettingsPage").then((m) => ({
    default: m.RoleSettingsPage,
  }))
);

function lazyPage(Component: ComponentType) {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <Component />
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <PublicLayout />,
    children: [
      { index: true, element: lazyPage(LandingPage) },
      { path: "features", element: lazyPage(FeaturesPage) },
      { path: "about", element: lazyPage(AboutPage) },
      { path: "contact", element: lazyPage(ContactPage) },
      { path: "unauthorized", element: lazyPage(UnauthorizedPage) },
      { path: "*", element: lazyPage(NotFoundPage) },
    ],
  },
  {
    element: <AuthLayout />,
    children: [
      {
        path: "login",
        element: (
          <GuestRoute>{lazyPage(LoginPage)}</GuestRoute>
        ),
      },
      {
        path: "register",
        element: (
          <GuestRoute>{lazyPage(RegisterPage)}</GuestRoute>
        ),
      },
    ],
  },
  {
    path: "/dashboard",
    element: (
      <ProtectedRoute allowedRoles={["citizen"]}>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="overview" replace /> },
      { path: "overview", element: lazyPage(DashboardOverviewPage) },
      { path: "pickups", element: lazyPage(CitizenPickupsPage) },
      { path: "pickups/new", element: lazyPage(NewPickupPage) },
      { path: "pickups/:id", element: lazyPage(PickupDetailsPage) },
      { path: "history", element: lazyPage(PickupHistoryPage) },
      { path: "profile", element: lazyPage(ProfilePage) },
      { path: "settings", element: lazyPage(RoleSettingsPage) },
    ],
  },
  {
    path: "/collector",
    element: (
      <ProtectedRoute allowedRoles={["collector"]}>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="overview" replace /> },
      { path: "overview", element: lazyPage(CollectorOverviewPage) },
      { path: "pickups/:id", element: lazyPage(CollectorPickupDetailsPage) },
      { path: "profile", element: lazyPage(RoleProfilePage) },
      { path: "settings", element: lazyPage(RoleSettingsPage) },
    ],
  },
  {
    path: "/dealer",
    element: (
      <ProtectedRoute allowedRoles={["dealer"]}>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="overview" replace /> },
      { path: "overview", element: lazyPage(DealerOverviewPage) },
      { path: "profile", element: lazyPage(RoleProfilePage) },
      { path: "settings", element: lazyPage(RoleSettingsPage) },
    ],
  },
  {
    path: "/admin",
    element: (
      <ProtectedRoute allowedRoles={["admin"]}>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="overview" replace /> },
      { path: "overview", element: lazyPage(AdminOverviewPage) },
      { path: "analytics", element: lazyPage(AIAnalyticsPage) },
      { path: "profile", element: lazyPage(RoleProfilePage) },
      { path: "settings", element: lazyPage(RoleSettingsPage) },
    ],
  },
]);
