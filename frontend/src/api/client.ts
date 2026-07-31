import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";
import { API_URL, REMEMBER_ME_KEY, TOKEN_STORAGE_KEY } from "@/lib/constants";

const REFRESH_TOKEN_STORAGE_KEY = "wasteiq_refresh_token";

export type TokenStorageMode = "local" | "session";

export interface AuthSession {
  accessToken: string;
  refreshToken?: string | null;
  storage?: TokenStorageMode;
}

export interface RefreshSessionResult {
  accessToken: string;
  refreshToken?: string | null;
}

export interface ApiErrorResponse {
  detail?: string | { msg?: string }[] | Record<string, unknown>;
  message?: string;
}

export interface ApiRequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean;
  _retry?: boolean;
}

type RefreshTokenHandler = (
  refreshToken: string
) => Promise<RefreshSessionResult | null>;

type UnauthorizedHandler = () => void;

function resolveApiBaseUrl(): string {
  return API_URL.trim().replace(/\/+$/, "");
}

function getStorage(mode: TokenStorageMode): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  return mode === "local" ? window.localStorage : window.sessionStorage;
}

function getRememberedStorageMode(): TokenStorageMode {
  if (typeof window === "undefined") {
    return "local";
  }

  return window.localStorage.getItem(REMEMBER_ME_KEY) === "false"
    ? "session"
    : "local";
}

function readStoredValue(key: string): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return (
    window.localStorage.getItem(key) ?? window.sessionStorage.getItem(key)
  );
}

interface JwtPayload {
  exp?: unknown;
}

function readJwtPayload(token: string): JwtPayload | null {
  if (typeof window === "undefined") {
    return null;
  }

  const encodedPayload = token.split(".")[1];

  if (!encodedPayload) {
    return null;
  }

  try {
    const base64 = encodedPayload
      .replace(/-/g, "+")
      .replace(/_/g, "/")
      .padEnd(Math.ceil(encodedPayload.length / 4) * 4, "=");

    return JSON.parse(window.atob(base64)) as JwtPayload;
  } catch {
    return null;
  }
}

export function isAccessTokenExpired(token: string, now = Date.now()): boolean {
  const payload = readJwtPayload(token);

  if (!payload || typeof payload.exp !== "number") {
    return true;
  }

  return payload.exp * 1_000 <= now;
}

function removeStoredValue(key: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(key);
  window.sessionStorage.removeItem(key);
}

export function getAccessToken(): string | null {
  const token = readStoredValue(TOKEN_STORAGE_KEY);

  if (token && isAccessTokenExpired(token)) {
    clearAuthSession();
    return null;
  }

  return token;
}

export function getRefreshToken(): string | null {
  return readStoredValue(REFRESH_TOKEN_STORAGE_KEY);
}

export function getAuthStorageMode(): TokenStorageMode {
  if (typeof window === "undefined") {
    return "local";
  }

  if (window.localStorage.getItem(TOKEN_STORAGE_KEY) !== null) {
    return "local";
  }

  if (window.sessionStorage.getItem(TOKEN_STORAGE_KEY) !== null) {
    return "session";
  }

  return getRememberedStorageMode();
}

export function clearAuthSession(): void {
  removeStoredValue(TOKEN_STORAGE_KEY);
  removeStoredValue(REFRESH_TOKEN_STORAGE_KEY);

  if (typeof window !== "undefined") {
    window.localStorage.removeItem(REMEMBER_ME_KEY);
  }
}

export function setAuthSession({
  accessToken,
  refreshToken,
  storage = "local",
}: AuthSession): void {
  clearAuthSession();

  const targetStorage = getStorage(storage);

  if (targetStorage === null) {
    return;
  }

  targetStorage.setItem(TOKEN_STORAGE_KEY, accessToken);

  if (refreshToken) {
    targetStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshToken);
  }

  window.localStorage.setItem(REMEMBER_ME_KEY, storage === "local" ? "true" : "false");
}

let refreshTokenHandler: RefreshTokenHandler | null = null;
let unauthorizedHandler: UnauthorizedHandler = () => {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("unauthorized"));
  }
};
let inflightRefreshPromise: Promise<string | null> | null = null;

export function configureRefreshHandler(
  handler: RefreshTokenHandler | null
): void {
  refreshTokenHandler = handler;
}

export function configureUnauthorizedHandler(
  handler: UnauthorizedHandler
): void {
  unauthorizedHandler = handler;
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();

  if (!refreshToken || refreshTokenHandler === null) {
    return null;
  }

  if (inflightRefreshPromise === null) {
    inflightRefreshPromise = refreshTokenHandler(refreshToken)
      .then((session) => {
        if (!session?.accessToken) {
          clearAuthSession();
          return null;
        }

        setAuthSession({
          accessToken: session.accessToken,
          refreshToken: session.refreshToken ?? refreshToken,
          storage: getAuthStorageMode(),
        });

        return session.accessToken;
      })
      .catch(() => {
        clearAuthSession();
        return null;
      })
      .finally(() => {
        inflightRefreshPromise = null;
      });
  }

  return inflightRefreshPromise;
}

function withAuthorizationHeader(
  config: InternalAxiosRequestConfig,
  token: string
): InternalAxiosRequestConfig {
  const headers = AxiosHeaders.from(config.headers);
  headers.set("Authorization", `Bearer ${token}`);

  return {
    ...config,
    headers,
  };
}

export const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 15000,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const requestConfig = config as InternalAxiosRequestConfig & ApiRequestConfig;

    if (requestConfig.skipAuth) {
      return requestConfig;
    }

    const token = getAccessToken();

    if (!token) {
      return requestConfig;
    }

    return withAuthorizationHeader(requestConfig, token);
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & ApiRequestConfig)
      | undefined;
    const status = error.response?.status;

    if (!originalRequest || status !== 401 || originalRequest.skipAuth) {
      return Promise.reject(error);
    }

    if (!originalRequest._retry) {
      originalRequest._retry = true;

      const nextAccessToken = await refreshAccessToken();

      if (nextAccessToken) {
        return apiClient(withAuthorizationHeader(originalRequest, nextAccessToken));
      }
    }

    clearAuthSession();
    unauthorizedHandler();

    return Promise.reject(error);
  }
);

export default apiClient;
