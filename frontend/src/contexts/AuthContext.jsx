import { createContext, useEffect, useState } from "react";

export const AuthContext = createContext(null);

const TOKEN_KEY = "wasteiq_token";
const USER_KEY = "wasteiq_user";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  });
  const [loading, setLoading] = useState(Boolean(token));

  async function getApi() {
    const module = await import("../api/client");
    return module.default;
  }

  useEffect(() => {
    async function syncUser() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const api = await getApi();
        const response = await api.get("/auth/me");
        setUser(response.data);
        localStorage.setItem(USER_KEY, JSON.stringify(response.data));
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    }

    syncUser();
  }, [token]);

  function persistSession(nextToken, nextUser) {
    localStorage.setItem(TOKEN_KEY, nextToken);
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
    setToken(nextToken);
    setUser(nextUser);
  }

  async function login(payload) {
    const api = await getApi();
    const response = await api.post("/auth/login", payload);
    persistSession(response.data.access_token, response.data.user);
    return response.data.user;
  }

  async function register(payload) {
    const api = await getApi();
    const response = await api.post("/auth/register", payload);
    persistSession(response.data.access_token, response.data.user);
    return response.data.user;
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loading,
        isAuthenticated: Boolean(token),
        login,
        register,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
