import { createContext, useContext, useState, useEffect, type ReactNode, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getProfile } from "../api/auth";
import type { UserProfile, UserRole } from "@/types/auth";
import {
  clearAuthSession,
  configureUnauthorizedHandler,
  getAccessToken,
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
  login: (token: string, user: User, rememberMe?: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => getAccessToken());
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
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
    configureUnauthorizedHandler(() => {
      logout();
    });

    return () => {
      configureUnauthorizedHandler(() => {
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("unauthorized"));
        }
      });
    };
  }, [logout]);

  const login = (newToken: string, newUser: User, rememberMe = true) => {
    setAuthSession({
      accessToken: newToken,
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

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
