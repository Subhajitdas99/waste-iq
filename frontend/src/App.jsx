import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";

const CitizenRequestDetailsPage = lazy(() => import("./pages/citizen/CitizenRequestDetailsPage"));
const CitizenRequestsPage = lazy(() => import("./pages/citizen/CitizenRequestsPage"));
const DashboardIndexPage = lazy(() => import("./pages/DashboardIndexPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const HomePage = lazy(() => import("./pages/HomePage"));
const LoginPage = lazy(() => import("./pages/auth/LoginPage"));
const RegisterPage = lazy(() => import("./pages/auth/RegisterPage"));

function RouteFallback() {
  return <div className="p-6 text-sm text-ink/70">Loading...</div>;
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardIndexPage />} />
          <Route path="requests" element={<CitizenRequestsPage />} />
          <Route path="requests/:requestId" element={<CitizenRequestDetailsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
