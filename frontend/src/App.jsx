import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import DashboardIndexPage from "./pages/DashboardIndexPage";
import DashboardPage from "./pages/DashboardPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/auth/LoginPage";
import CitizenRequestDetailsPage from "./pages/citizen/CitizenRequestDetailsPage";
import CitizenRequestsPage from "./pages/citizen/CitizenRequestsPage";
import RegisterPage from "./pages/auth/RegisterPage";

export default function App() {
  return (
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
  );
}
