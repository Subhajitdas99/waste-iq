import { afterEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { server } from "./server";
import { createTestQueryClient } from "./test-utils";
import { createPickupRequest } from "./factories";
import { AuthProvider } from "@/context/AuthContext";
import { useBrowserGeolocation } from "@/hooks/useBrowserGeolocation";
import { useRegister } from "@/hooks/useRegister";
import {
  useCancelCitizenPickup,
  useCitizenPickupDetail,
  useCitizenPickups,
  useCitizenPickupSummary,
  useUpdateCitizenPickup,
} from "@/hooks/useCitizenPickups";
import { getAccessToken } from "@/api/client";
import type { PickupRequest } from "@/types/pickup";

function renderWithProviders(client: QueryClient, ui: React.ReactElement) {
  return render(
    <QueryClientProvider client={client}>
      <AuthProvider>{ui}</AuthProvider>
    </QueryClientProvider>,
  );
}

describe("useBrowserGeolocation", () => {
  function stubGeolocation(impl: {
    success?: { latitude: number; longitude: number };
    error?: { message: string };
  }) {
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: {
        getCurrentPosition: (onSuccess: PositionCallback, onError?: PositionErrorCallback) => {
          if (impl.success) {
            onSuccess({
              coords: { latitude: impl.success.latitude, longitude: impl.success.longitude },
              timestamp: Date.now(),
            } as GeolocationPosition);
          } else if (impl.error) {
            onError?.({ message: impl.error.message } as GeolocationPositionError);
          }
        },
      },
    });
  }

  afterEach(() => {
    Reflect.deleteProperty(navigator, "geolocation");
  });

  it("reports an error when geolocation is unsupported", async () => {
    const user = userEvent.setup();
    function Harness() {
      const { error, requestLocation } = useBrowserGeolocation();
      return (
        <div>
          <button type="button" onClick={requestLocation}>
            Locate
          </button>
          <p data-testid="error">{error ?? "no error"}</p>
        </div>
      );
    }
    renderWithProviders(createTestQueryClient(), <Harness />);

    await user.click(screen.getByRole("button", { name: "Locate" }));

    expect(screen.getByTestId("error")).toHaveTextContent(
      "Geolocation is not supported in this browser.",
    );
  });

  it("resolves the position on success", async () => {
    stubGeolocation({ success: { latitude: 22.5726, longitude: 88.3639 } });
    const user = userEvent.setup();
    function Harness() {
      const { position, error, isLocating, requestLocation } = useBrowserGeolocation();
      return (
        <div>
          <button type="button" onClick={requestLocation}>
            Locate
          </button>
          <p data-testid="position">
            {position ? `${position.latitude},${position.longitude}` : "none"}
          </p>
          <p data-testid="error">{error ?? "no error"}</p>
          <p data-testid="locating">{String(isLocating)}</p>
        </div>
      );
    }
    renderWithProviders(createTestQueryClient(), <Harness />);

    await user.click(screen.getByRole("button", { name: "Locate" }));

    expect(screen.getByTestId("position")).toHaveTextContent("22.5726,88.3639");
    expect(screen.getByTestId("error")).toHaveTextContent("no error");
    expect(screen.getByTestId("locating")).toHaveTextContent("false");
  });

  it("surfaces the geolocation error message on failure", async () => {
    stubGeolocation({ error: { message: "User denied the request" } });
    const user = userEvent.setup();
    function Harness() {
      const { position, error, requestLocation } = useBrowserGeolocation();
      return (
        <div>
          <button type="button" onClick={requestLocation}>
            Locate
          </button>
          <p data-testid="position">{position ? "positioned" : "none"}</p>
          <p data-testid="error">{error ?? "no error"}</p>
        </div>
      );
    }
    renderWithProviders(createTestQueryClient(), <Harness />);

    await user.click(screen.getByRole("button", { name: "Locate" }));

    expect(screen.getByTestId("position")).toHaveTextContent("none");
    expect(screen.getByTestId("error")).toHaveTextContent("User denied the request");
  });
});

describe("useRegister", () => {
  function RegisterHarness({ autoLogin = false, rememberMe = false }) {
    const mutation = useRegister();
    return (
      <div>
        <button
          type="button"
          onClick={() =>
            mutation.mutate({
              email: "new@example.com",
              name: "New Citizen",
              phone: "+15551234567",
              password: "strong-password",
              role: "citizen",
              autoLogin,
              rememberMe,
            })
          }
        >
          Register
        </button>
        {mutation.isSuccess ? <p data-testid="success">registered</p> : null}
        {mutation.isError ? <p data-testid="error">failed</p> : null}
      </div>
    );
  }

  it("registers without auto-login", async () => {
    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <RegisterHarness />);

    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(await screen.findByTestId("success")).toBeInTheDocument();
    expect(getAccessToken()).toBeNull();
  });

  it("auto-logs-in and persists the session when requested", async () => {
    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <RegisterHarness autoLogin rememberMe />);

    await user.click(screen.getByRole("button", { name: "Register" }));

    await waitFor(() => {
      expect(getAccessToken()).not.toBeNull();
    });
  });

  it("surfaces registration failures", async () => {
    server.use(
      http.post("*/auth/register", () =>
        HttpResponse.json({ detail: "Email already registered" }, { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <RegisterHarness />);

    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(await screen.findByTestId("error")).toBeInTheDocument();
    expect(getAccessToken()).toBeNull();
  });
});

describe("pickup mutations", () => {
  const requestFixture = createPickupRequest({ id: 1 });

  it("updates a pickup request and invalidates the list and detail", async () => {
    let listCalls = 0;
    let updatedAddress = "12 Green Street, Kolkata";
    server.use(
      http.get("*/pickup-requests", () => {
        listCalls += 1;
        return HttpResponse.json([{ ...requestFixture, address: updatedAddress }]);
      }),
      http.get("*/pickup-requests/citizen/summary", () =>
        HttpResponse.json({
          total_requests: 1,
          pending_requests: 1,
          accepted_requests: 0,
          completed_requests: 0,
        }),
      ),
      http.get("*/pickup-requests/1", () =>
        HttpResponse.json({ ...requestFixture, address: updatedAddress, timeline: [] }),
      ),
      http.patch("*/pickup-requests/1", async ({ request }) => {
        const body = (await request.json()) as { address?: string };
        updatedAddress = body.address ?? updatedAddress;
        return HttpResponse.json({ ...requestFixture, address: updatedAddress });
      }),
    );

    function UpdateHarness() {
      const listQuery = useCitizenPickups();
      const detailQuery = useCitizenPickupDetail(1);
      const updateMutation = useUpdateCitizenPickup();
      return (
        <div>
          <p data-testid="address">{listQuery.data?.[0]?.address ?? "none"}</p>
          <p data-testid="detail">{detailQuery.data?.status ?? "none"}</p>
          <button
            type="button"
            onClick={() =>
              updateMutation.mutate({ requestId: 1, payload: { address: "9 New Lane" } })
            }
          >
            Update
          </button>
        </div>
      );
    }

    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <UpdateHarness />);

    await waitFor(() => {
      expect(screen.getByTestId("address")).toHaveTextContent("12 Green Street");
    });
    expect(listCalls).toBe(1);

    await user.click(screen.getByRole("button", { name: "Update" }));

    await waitFor(() => {
      expect(screen.getByTestId("address")).toHaveTextContent("9 New Lane");
    });
    expect(listCalls).toBeGreaterThanOrEqual(2);
    expect(screen.getByTestId("detail")).toHaveTextContent("pending");
  });

  it("optimistically cancels a pickup and rolls back on failure", async () => {
    let cancelled = false;
    let shouldFailCancel = true;
    server.use(
      http.get("*/pickup-requests", () =>
        HttpResponse.json([
          { ...requestFixture, status: cancelled ? "cancelled" : "pending", can_cancel: !cancelled },
        ] as PickupRequest[]),
      ),
      http.get("*/pickup-requests/citizen/summary", () =>
        HttpResponse.json({
          total_requests: 1,
          pending_requests: cancelled ? 0 : 1,
          accepted_requests: 0,
          completed_requests: 0,
        }),
      ),
      http.get("*/pickup-requests/1", () =>
        HttpResponse.json({
          ...requestFixture,
          status: cancelled ? "cancelled" : "pending",
          can_cancel: !cancelled,
          timeline: [],
        }),
      ),
      http.post("*/pickup-requests/1/cancel", () => {
        if (shouldFailCancel) {
          return HttpResponse.json({ detail: "Cannot cancel" }, { status: 400 });
        }
        cancelled = true;
        return HttpResponse.json({
          ...requestFixture,
          status: "cancelled",
          can_cancel: false,
        });
      }),
    );

    function CancelHarness() {
      const listQuery = useCitizenPickups();
      const summaryQuery = useCitizenPickupSummary();
      const detailQuery = useCitizenPickupDetail(1);
      const cancelMutation = useCancelCitizenPickup();
      return (
        <div>
          <p data-testid="status">{listQuery.data?.[0]?.status ?? "none"}</p>
          <p data-testid="summary-pending">
            {summaryQuery.data?.pending_requests ?? "-"}
          </p>
          <p data-testid="detail-status">{detailQuery.data?.status ?? "none"}</p>
          <button type="button" onClick={() => cancelMutation.mutate(1)}>
            Cancel
          </button>
        </div>
      );
    }

    const user = userEvent.setup();
    renderWithProviders(createTestQueryClient(), <CancelHarness />);

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("pending");
    });

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("pending");
    });
    expect(screen.getByTestId("summary-pending")).toHaveTextContent("1");
    expect(screen.getByTestId("detail-status")).toHaveTextContent("pending");

    shouldFailCancel = false;
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("cancelled");
    });
    expect(screen.getByTestId("summary-pending")).toHaveTextContent("0");
    expect(screen.getByTestId("detail-status")).toHaveTextContent("cancelled");
  });
});
