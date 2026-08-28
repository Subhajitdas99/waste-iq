import { beforeEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { server } from "./server";
import { renderApp, storeValidSession } from "./test-utils";
import { resetPickupStore } from "./handlers";
import { createPickupRequest } from "./factories";

describe("citizen UX hardening", () => {
  beforeEach(() => {
    resetPickupStore();
  });

  it("renders a helpful empty state when the citizen has no pickups", async () => {
    server.use(
      http.get("*/pickup-requests", () => HttpResponse.json([])),
      http.get("*/pickup-requests/citizen/summary", () =>
        HttpResponse.json({
          total_requests: 0,
          pending_requests: 0,
          accepted_requests: 0,
          completed_requests: 0,
        }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/pickups");

    expect(
      await screen.findByText(/You haven't created a pickup yet/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Create Your First Pickup/i }),
    ).toBeInTheDocument();
  });

  it("renders an error state with a retry button when the pickups list fails to load", async () => {
    server.use(
      http.get("*/pickup-requests", () =>
        HttpResponse.json({ detail: "Network unreachable" }, { status: 503 }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/pickups");

    expect(
      await screen.findByText(/Unable to load pickup requests/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Try again/i })).toBeInTheDocument();
  });

  it("displays the weight comparison on the pickup details page when weight is recorded", async () => {
    server.use(
      http.get("*/pickup-requests/1", () =>
        HttpResponse.json({
          ...createPickupRequest({
            id: 1,
            status: "weight_recorded",
            estimated_weight_kg: 5.0,
            can_cancel: false,
            assignment: {
              id: 11,
              collector_id: 2,
              collector_name: "Test Collector",
              accepted_at: "2026-01-10T08:00:00Z",
              completed_at: null,
              weight_kg: 8.2,
            },
          }),
          timeline: [],
          dispute: null,
        }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/pickups/1");

    expect(
      await screen.findByText("Weight Verification"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("8.2 kg").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/Confirming accepts the recorded weight/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Confirm Weight/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Dispute Weight/i }),
    ).toBeInTheDocument();
  });

  it("displays dispute reason guidance in the modal", async () => {
    server.use(
      http.get("*/pickup-requests/1", () =>
        HttpResponse.json({
          ...createPickupRequest({
            id: 1,
            status: "weight_recorded",
            can_cancel: false,
            assignment: {
              id: 11,
              collector_id: 2,
              collector_name: "Test Collector",
              accepted_at: "2026-01-10T08:00:00Z",
              completed_at: null,
              weight_kg: 8.2,
            },
          }),
          timeline: [],
          dispute: null,
        }),
      ),
    );

    const user = userEvent.setup();
    storeValidSession("citizen");
    await renderApp("/dashboard/pickups/1");

    expect(await screen.findByText("Weight Verification")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Dispute Weight/i }));

    expect(screen.getByText(/Minimum 5 characters required/i)).toBeInTheDocument();
    expect(screen.getByText(/0 \/ 2000/)).toBeInTheDocument();
  });

  it("displays the disputed state with guidance message", async () => {
    server.use(
      http.get("*/pickup-requests/1", () =>
        HttpResponse.json({
          ...createPickupRequest({
            id: 1,
            status: "disputed",
            can_cancel: false,
            assignment: {
              id: 11,
              collector_id: 2,
              collector_name: "Test Collector",
              accepted_at: "2026-01-10T08:00:00Z",
              completed_at: null,
              weight_kg: 8.2,
            },
          }),
          timeline: [],
          dispute: {
            id: 22,
            request_id: 1,
            reason: "The weight seems incorrect.",
            disputed_at: "2026-01-12T10:00:00Z",
            resolved_at: null,
            resolution: null,
            resolved_weight_kg: null,
            resolution_notes: null,
            resolved_by_id: null,
          },
        }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/pickups/1");

    expect(await screen.findByText("Weight Disputed")).toBeInTheDocument();
    expect(
      screen.getByText(/Your dispute has been submitted and is being reviewed/i),
    ).toBeInTheDocument();
  });

  it("does not show the Contact Collector button before the request is accepted", async () => {
    server.use(
      http.get("*/pickup-requests/1", () =>
        HttpResponse.json({
          ...createPickupRequest({
            id: 1,
            status: "pending",
            can_cancel: true,
          }),
          timeline: [],
          dispute: null,
        }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/pickups/1");

    expect(
      await screen.findByRole("heading", { name: /Pickup Request #1/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Contact Collector/i }),
    ).not.toBeInTheDocument();
  });

  it("shows the Contact Collector button once the request is accepted", async () => {
    server.use(
      http.get("*/pickup-requests/1", () =>
        HttpResponse.json({
          ...createPickupRequest({
            id: 1,
            status: "accepted",
            can_cancel: false,
            assigned_collector_name: "Test Collector",
            assignment: {
              id: 11,
              collector_id: 2,
              collector_name: "Test Collector",
              accepted_at: "2026-01-10T08:00:00Z",
              completed_at: null,
              weight_kg: null,
            },
          }),
          timeline: [],
          dispute: null,
        }),
      ),
    );

    storeValidSession("citizen");
    await renderApp("/dashboard/pickups/1");

    expect(
      screen.getAllByRole("button", { name: /Contact Collector/i }).length,
    ).toBeGreaterThan(0);
  });
});
