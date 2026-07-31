import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, beforeEach, vi } from "vitest";
import { server } from "./server";

if (typeof window !== "undefined" && !window.ResizeObserver) {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }

  window.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
}

if (typeof window !== "undefined" && !window.IntersectionObserver) {
  class IntersectionObserverStub {
    readonly root = null;
    readonly rootMargin = "";
    readonly thresholds = [];

    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  }

  window.IntersectionObserver =
    IntersectionObserverStub as unknown as typeof IntersectionObserver;
}

if (typeof window !== "undefined" && !window.matchMedia) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

beforeAll(async () => {
  await Promise.all([
    import("../pages/auth/LoginPage"),
    import("../pages/auth/RegisterPage"),
    import("../pages/dashboard/DashboardOverviewPage"),
    import("../pages/dashboard/CollectorOverviewPage"),
    import("../pages/dashboard/DealerOverviewPage"),
    import("../pages/dashboard/AdminOverviewPage"),
    import("../pages/dashboard/CitizenPickupsPage"),
    import("../pages/dashboard/NewPickupPage"),
    import("../pages/dashboard/PickupDetailsPage"),
    import("../pages/dashboard/PickupHistoryPage"),
    import("../pages/dashboard/ProfilePage"),
    import("../pages/dashboard/SettingsPage"),
    import("../pages/dashboard/RoleProfilePage"),
    import("../pages/dashboard/RoleSettingsPage"),
    import("../pages/public/LandingPage"),
    import("../pages/public/FeaturesPage"),
    import("../pages/public/AboutPage"),
    import("../pages/public/ContactPage"),
    import("../pages/public/NotFoundPage"),
  ]);
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  server.resetHandlers();
  cleanup();
  window.localStorage.clear();
  window.sessionStorage.clear();
  vi.restoreAllMocks();
});

afterAll(() => {
  server.close();
});

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
  window.history.pushState({}, "", "/");
});
