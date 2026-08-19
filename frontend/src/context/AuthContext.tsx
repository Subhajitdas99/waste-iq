import { createContext, useContext, useState, useEffect, type ReactNode, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  getProfile,
  logout as logoutRequest,
  refresh as refreshRequest,
} from "../api/auth";
import type { UserProfile, UserRole } from "@/types/auth";
import {
  clearAuthSession,
  configureRefreshHandler,
  configureUnauthorizedHandler,
  getAccessToken,
  getRefreshToken,
  setAuthSession,
} from "../api/client";
import { authQueryKeys } from "../hooks/auth-query-keys";

export type Role = UserRole;

export type User = UserProfile;

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: User, rememberMe?: boolean, refreshToken?: string | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => getAccessToken());
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    // Best-effort server-side revocation of the current refresh session.
    // Fire-and-forget: local logout must succeed even when the network is
    // unavailable or the token is already revoked.
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      logoutRequest(refreshToken).catch(() => undefined);
    }
    clearAuthSession();
    setToken(null);
    setUser(null);
    setIsLoading(false);
    queryClient.removeQueries({ queryKey: authQueryKeys.currentUser });
  }, [queryClient]);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    let isActive = true;

    setIsLoading(true);

    getProfile()
      .then((profile) => {
        if (!isActive) {
          return;
        }

        setUser(profile);
        queryClient.setQueryData(authQueryKeys.currentUser, profile);
      })
      .catch(() => {
        if (!isActive) {
          return;
        }

        logout();
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, logout, queryClient]);

  useEffect(() => {
    // Wire the client's inflight-refresh dedupe to the real /auth/refresh
    // endpoint. The handler returns the rotated pair; a failed exchange
    // clears the session and triggers logout.
    configureRefreshHandler(async (refreshToken) => {
      try {
        const response = await refreshRequest(refreshToken);
        return {
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
        };
      } catch {
        return null;
      }
    });

    configureUnauthorizedHandler(() => {
      logout();
    });

    return () => {
      configureRefreshHandler(null);
      configureUnauthorizedHandler(() => {
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("unauthorized"));
        }
      });
    };
  }, [logout]);

  const login = (newToken: string, newUser: User, rememberMe = true, refreshToken?: string | null) => {
    setAuthSession({
      accessToken: newToken,
      refreshToken: refreshToken ?? null,
      storage: rememberMe ? "local" : "session",
    });
    setToken(newToken);
    setUser(newUser);
    setIsLoading(false);
    queryClient.setQueryData(authQueryKeys.currentUser, newUser);
  };

  const isAuthenticated = Boolean(token && user);

  return (
    <AuthContext.Provider
      value={{ user, token, isAuthenticated, isLoading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components -- hooks must live with their provider to keep a single import path for consumers
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
