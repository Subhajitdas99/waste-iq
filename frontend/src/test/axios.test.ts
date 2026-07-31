import { afterEach, describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import {
  apiClient,
  clearAuthSession,
  configureRefreshHandler,
  getAccessToken,
  getRefreshToken,
  isAccessTokenExpired,
  setAuthSession,
  type ApiRequestConfig,
} from "@/api/client";
import { server } from "./server";
import { EXPIRED_TOKEN, VALID_TOKEN } from "./factories";
import { TOKEN_STORAGE_KEY } from "@/lib/constants";

const REFRESH_TOKEN = "refresh-token-1";
const REFRESH_TOKEN_STORAGE_KEY = "wasteiq_refresh_token";

afterEach(() => {
  configureRefreshHandler(null);
  window.removeEventListener("unauthorized", handleUnauthorized);
});

function handleUnauthorized() {
  /* registered per-test to observe the 401 logout signal */
}

describe("axios request interceptor", () => {
  it("attaches the Bearer token to authenticated requests", async () => {
    let capturedAuthorization: string | null = null;
    server.use(
      http.get("*/auth/me", ({ request }) => {
        capturedAuthorization = request.headers.get("authorization");
        return HttpResponse.json({ id: 1, name: "Test Citizen", role: "citizen" });
      }),
    );
    setAuthSession({ accessToken: VALID_TOKEN, refreshToken: REFRESH_TOKEN, storage: "local" });

    await apiClient.get("/auth/me");

    expect(capturedAuthorization).toBe(`Bearer ${VALID_TOKEN}`);
  });

  it("omits the Authorization header when no token is stored", async () => {
    let capturedAuthorization: string | null = "sentinel";
    server.use(
      http.get("*/auth/me", ({ request }) => {
        capturedAuthorization = request.headers.get("authorization");
        return HttpResponse.json({ id: 1 });
      }),
    );

    await apiClient.get("/auth/me");

    expect(capturedAuthorization).toBeNull();
  });

  it("omits the Authorization header when the request is marked skipAuth", async () => {
    let capturedAuthorization: string | null = "sentinel";
    server.use(
      http.get("*/auth/me", ({ request }) => {
        capturedAuthorization = request.headers.get("authorization");
        return HttpResponse.json({ id: 1 });
      }),
    );
    setAuthSession({ accessToken: VALID_TOKEN, storage: "local" });

    await apiClient.get("/auth/me", { skipAuth: true } as ApiRequestConfig);

    expect(capturedAuthorization).toBeNull();
  });

  it("clears an expired stored token before sending the request", async () => {
    let capturedAuthorization: string | null = "sentinel";
    server.use(
      http.get("*/auth/me", ({ request }) => {
        capturedAuthorization = request.headers.get("authorization");
        return HttpResponse.json({ id: 1 });
      }),
    );
    setAuthSession({ accessToken: EXPIRED_TOKEN, storage: "local" });

    const response = await apiClient.get("/auth/me");

    expect(capturedAuthorization).toBeNull();
    expect(response.data).toEqual({ id: 1 });
    expect(getAccessToken()).toBeNull();
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
  });
});

describe("axios response interceptor", () => {
  it("rejects a 401, clears the session, and fires the unauthorized event when refresh fails", async () => {
    const unauthorizedSpy = vi.fn();
    window.addEventListener("unauthorized", unauthorizedSpy);
    server.use(
      http.get("*/pickup-requests", () =>
        HttpResponse.json({ detail: "Not authenticated" }, { status: 401 }),
      ),
    );
    setAuthSession({ accessToken: VALID_TOKEN, refreshToken: REFRESH_TOKEN, storage: "local" });

    await expect(apiClient.get("/pickup-requests")).rejects.toMatchObject({
      response: { status: 401 },
    });

    expect(unauthorizedSpy).toHaveBeenCalledTimes(1);
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it("retries the original request with a refreshed token and does not log out", async () => {
    let callCount = 0;
    const capturedAuthorizations: (string | null)[] = [];
    const refreshSpy = vi.fn(async (refreshToken: string) => {
      expect(refreshToken).toBe(REFRESH_TOKEN);
      return { accessToken: VALID_TOKEN, refreshToken: "refresh-token-2" };
    });
    configureRefreshHandler(refreshSpy);
    server.use(
      http.get("*/pickup-requests", ({ request }) => {
        callCount += 1;
        capturedAuthorizations.push(request.headers.get("authorization"));
        if (callCount === 1) {
          return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
        }
        return HttpResponse.json([{ id: 1, waste_type: "Plastic bottles" }]);
      }),
    );
    setAuthSession({ accessToken: VALID_TOKEN, refreshToken: REFRESH_TOKEN, storage: "local" });

    const response = await apiClient.get("/pickup-requests");

    expect(response.status).toBe(200);
    expect(response.data).toEqual([{ id: 1, waste_type: "Plastic bottles" }]);
    expect(callCount).toBe(2);
    expect(capturedAuthorizations[0]).toBe(`Bearer ${VALID_TOKEN}`);
    expect(capturedAuthorizations[1]).toBe(`Bearer ${VALID_TOKEN}`);
    expect(refreshSpy).toHaveBeenCalledTimes(1);
    expect(getAccessToken()).toBe(VALID_TOKEN);
    expect(getRefreshToken()).toBe("refresh-token-2");
  });

  it("does not attempt refresh for non-401 errors", async () => {
    const refreshSpy = vi.fn();
    configureRefreshHandler(refreshSpy);
    server.use(
      http.get("*/pickup-requests", () =>
        HttpResponse.json({ detail: "Server exploded" }, { status: 500 }),
      ),
    );
    setAuthSession({ accessToken: VALID_TOKEN, storage: "local" });

    await expect(apiClient.get("/pickup-requests")).rejects.toMatchObject({
      response: { status: 500 },
    });

    expect(refreshSpy).not.toHaveBeenCalled();
    expect(getAccessToken()).toBe(VALID_TOKEN);
  });
});

describe("auth session storage helpers", () => {
  it("stores the token and refresh token in the chosen storage", () => {
    setAuthSession({ accessToken: VALID_TOKEN, refreshToken: REFRESH_TOKEN, storage: "session" });

    expect(window.sessionStorage.getItem(TOKEN_STORAGE_KEY)).toBe(VALID_TOKEN);
    expect(window.sessionStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)).toBe(REFRESH_TOKEN);
    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
    expect(getAccessToken()).toBe(VALID_TOKEN);
    expect(getRefreshToken()).toBe(REFRESH_TOKEN);
  });

  it("clears tokens from both storages", () => {
    setAuthSession({ accessToken: VALID_TOKEN, refreshToken: REFRESH_TOKEN, storage: "local" });
    window.sessionStorage.setItem(TOKEN_STORAGE_KEY, "stale-session-token");

    clearAuthSession();

    expect(window.localStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
    expect(window.sessionStorage.getItem(TOKEN_STORAGE_KEY)).toBeNull();
    expect(window.localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)).toBeNull();
    expect(window.sessionStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)).toBeNull();
    expect(getAccessToken()).toBeNull();
  });

  it("reports token expiry from the JWT exp claim", () => {
    expect(isAccessTokenExpired(EXPIRED_TOKEN)).toBe(true);
    expect(isAccessTokenExpired(VALID_TOKEN)).toBe(false);
    expect(isAccessTokenExpired("malformed-token")).toBe(true);
  });
});
