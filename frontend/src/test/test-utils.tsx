import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, type RenderResult } from "@testing-library/react";
import { HelmetProvider } from "react-helmet-async";
import { RouterProvider } from "react-router-dom";
import { QueryErrorToastProvider } from "@/components/QueryErrorToastProvider";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import { router } from "@/routes";
import { createAppQueryClient } from "@/queryClient";
import { TOKEN_STORAGE_KEY } from "@/lib/constants";
import { setAuthSession } from "@/api/client";
import { usersByRole, createTestToken, type TestTokenOptions } from "./factories";
import type { UserProfile, UserRole } from "@/types/auth";

const TEST_STORAGE_KEY = "test-theme-key";

export function createTestQueryClient(): QueryClient {
  return createAppQueryClient({
    queries: {
      retry: false,
      staleTime: 60_000,
      gcTime: 0,
    },
    mutations: {
      retry: false,
    },
  });
}

export async function renderApp(initialPath = "/"): Promise<RenderResult> {
  const view = render(
    <HelmetProvider>
      <QueryClientProvider client={createTestQueryClient()}>
        <ThemeProvider defaultTheme="light" storageKey={TEST_STORAGE_KEY}>
          <AuthProvider>
            <QueryErrorToastProvider />
            <RouterProvider router={router} />
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </HelmetProvider>,
  );

  await act(async () => {
    router.navigate(initialPath);
  });

  return view;
}

export function storeValidSession(
  role: UserRole = "citizen",
  tokenOptions: TestTokenOptions = {},
): UserProfile {
  const user = usersByRole[role];
  setAuthSession({
    accessToken: createTestToken({ sub: String(user.id), ...tokenOptions }),
    storage: "local",
  });
  return user;
}

export function storeRawToken(token: string): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export { router };
