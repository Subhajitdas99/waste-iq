import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import api from "../api/axios";
import {
  TOKEN_STORAGE_KEY,
  REMEMBER_ME_KEY,
} from "../lib/constants";

export type Role = "citizen" | "collector" | "dealer" | "admin";

export interface User {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: Role;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User, rememberMe?: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function getStoredToken(): string | null {
  return (
    localStorage.getItem(TOKEN_STORAGE_KEY) ??
    sessionStorage.getItem(TOKEN_STORAGE_KEY)
  );
}

function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(REMEMBER_ME_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getStoredToken);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    api
      .get<User>("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => logout())
      .finally(() => setIsLoading(false));
  }, [token, logout]);

  useEffect(() => {
    const handleUnauthorized = () => logout();
    window.addEventListener("unauthorized", handleUnauthorized);
    return () => window.removeEventListener("unauthorized", handleUnauthorized);
  }, [logout]);

  const login = (newToken: string, newUser: User, rememberMe = true) => {
    clearStoredToken();

    if (rememberMe) {
      localStorage.setItem(TOKEN_STORAGE_KEY, newToken);
      localStorage.setItem(REMEMBER_ME_KEY, "true");
    } else {
      sessionStorage.setItem(TOKEN_STORAGE_KEY, newToken);
      localStorage.setItem(REMEMBER_ME_KEY, "false");
    }

    setToken(newToken);
    setUser(newUser);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
