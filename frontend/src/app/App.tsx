import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { router } from "../routes";
import { QueryErrorToastProvider } from "../components/QueryErrorToastProvider";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { AuthProvider } from "../context/AuthContext";
import { ThemeProvider } from "../context/ThemeContext";
import { queryClient } from "../queryClient";

export function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider defaultTheme="system" storageKey="wasteiq-ui-theme">
          <AuthProvider>
            <QueryErrorToastProvider />
            <RouterProvider router={router} />
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
