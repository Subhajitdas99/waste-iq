import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { listAdminDisputedPickups, resolveAdminWeightDispute } from "@/api/admin";
import { WeightDisputeCard } from "@/components/dashboard/WeightDisputeCard";
import { WeightDisputeDialog } from "@/components/dashboard/WeightDisputeDialog";
import type { AdminDisputedPickup } from "@/types/pickup";
import { server } from "./server";
import { createPickupRequest } from "./factories";
import { renderApp, storeValidSession } from "./test-utils";

const disputedPickup: AdminDisputedPickup = {
  ...createPickupRequest({
    id: 117,
    status: "disputed",
    waste_type: "Plastic bottles",
    citizen_name: "Asha Citizen",
    estimated_weight_kg: 5,
    assigned_collector_name: "Ravi Collector",
    assignment: {
      id: 7,
      collector_id: 4,
      collector_name: "Ravi Collector",
      accepted_at: "2026-09-08T08:00:00Z",
      completed_at: "2026-09-08T10:00:00Z",
      weight_kg: 3.5,
    },
  }),
  dispute: {
    id: 12,
    request_id: 117,
    reason: "wrong weight",
    disputed_at: "2026-09-08T11:00:00Z",
    resolved_at: null,
    resolution: null,
    resolved_weight_kg: null,
    resolution_notes: null,
    resolved_by_id: null,
  },
};

describe("admin weight dispute API", () => {
  it("lists the paginated dispute queue", async () => {
    server.use(
      http.get("*/admin/disputes/pickups", ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get("page")).toBe("2");
        expect(url.searchParams.get("page_size")).toBe("10");
        return HttpResponse.json({
          items: [disputedPickup],
          page: 2,
          page_size: 10,
          total_items: 11,
          total_pages: 2,
        });
      }),
    );

    const page = await listAdminDisputedPickups(2, 10);
    expect(page.items[0].dispute.reason).toBe("wrong weight");
    expect(page.total_pages).toBe(2);
  });

  it("submits an admin resolution payload", async () => {
    server.use(
      http.post("*/admin/disputes/pickups/117/resolve", async ({ request }) => {
        expect(await request.json()).toEqual({
          resolution: "corrected",
          resolved_weight_kg: 4,
          notes: "Adjusted after review.",
        });
        return HttpResponse.json({});
      }),
    );

    await expect(
      resolveAdminWeightDispute(117, {
        resolution: "corrected",
        resolved_weight_kg: 4,
        notes: "Adjusted after review.",
      }),
    ).resolves.toBeUndefined();
  });
});

describe("weight dispute review UI", () => {
  it("renders the comparison, reason, and resolution actions", () => {
    render(
      <WeightDisputeCard
        request={disputedPickup}
        onUphold={vi.fn()}
        onCorrect={vi.fn()}
      />,
    );

    expect(screen.getByText("Request #117")).toBeInTheDocument();
    expect(screen.getByText("Difference: 1.5 kg")).toBeInTheDocument();
    expect(screen.getByText("wrong weight")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Uphold Weight" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Correct Weight" })).toBeEnabled();
  });

  it("submits an uphold resolution with optional notes", () => {
    const onConfirm = vi.fn();
    render(
      <WeightDisputeDialog
        isOpen
        mode="upheld"
        requestId={117}
        disputeReason="wrong weight"
        collectorWeightKg={3.5}
        collectorName="Ravi Collector"
        onConfirm={onConfirm}
        onClose={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("Admin notes"), {
      target: { value: "Measurement verified." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Uphold Weight" }));
    expect(onConfirm).toHaveBeenCalledWith({
      resolution: "upheld",
      resolved_weight_kg: null,
      notes: "Measurement verified.",
    });
  });

  it("validates corrected weight before submitting", () => {
    const onConfirm = vi.fn();
    render(
      <WeightDisputeDialog
        isOpen
        mode="corrected"
        requestId={117}
        disputeReason="wrong weight"
        collectorWeightKg={3.5}
        collectorName="Ravi Collector"
        onConfirm={onConfirm}
        onClose={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Correct Weight" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Corrected weight is required");
    expect(onConfirm).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Corrected weight (kg)"), {
      target: { value: "4" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Correct Weight" }));
    expect(onConfirm).toHaveBeenCalledWith({
      resolution: "corrected",
      resolved_weight_kg: 4,
      notes: null,
    });
  });

  it("shows resolution API errors", () => {
    render(
      <WeightDisputeDialog
        isOpen
        mode="upheld"
        requestId={117}
        disputeReason="wrong weight"
        collectorWeightKg={3.5}
        collectorName="Ravi Collector"
        apiError="The dispute is no longer pending."
        onConfirm={vi.fn()}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("The dispute is no longer pending.");
  });

  it("shows an empty dispute queue on the admin dashboard", async () => {
    server.use(
      http.get("*/admin/analytics/pilot", () =>
        HttpResponse.json({ detail: "Pilot metrics unavailable" }, { status: 500 }),
      ),
    );
    storeValidSession("admin");
    await renderApp("/admin/overview");

    expect(await screen.findByText("No weight disputes")).toBeInTheDocument();
  });
});
