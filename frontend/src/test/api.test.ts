import { describe, expect, it, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "./server";
import {
  getCollectorSummary,
  listAvailableCollectorRequests,
} from "@/api/collector";
import {
  cancelPickupRequest,
  createPickupRequest,
  getCitizenRequestSummary,
  getPickupRequestDetail,
  listPickupRequests,
  updatePickupRequest,
} from "@/api/pickupRequests";
import { createPickupRequest as createPickupRequestFixture } from "./factories";

describe("collector API", () => {
  it("fetches the collector summary", async () => {
    const summary = await getCollectorSummary();
    expect(summary.total_assigned).toBe(10);
    expect(summary.active_jobs).toBe(3);
  });

  it("lists available collector requests", async () => {
    const requests = await listAvailableCollectorRequests();
    expect(requests.map((request) => request.waste_type)).toEqual([
      "Cardboard",
      "Glass bottles",
    ]);
  });
});

describe("pickup requests API", () => {
  it("lists pickup requests and the citizen summary", async () => {
    const requests = await listPickupRequests();
    expect(requests).toHaveLength(2);
    expect(requests[1].waste_type).toBe("Cardboard");

    const summary = await getCitizenRequestSummary();
    expect(summary.total_requests).toBe(5);
  });

  it("fetches a single pickup request detail", async () => {
    server.use(
      http.get("*/pickup-requests/42", () =>
        HttpResponse.json(createPickupRequestFixture({ id: 42 })),
      ),
    );

    const detail = await getPickupRequestDetail(42);
    expect(detail.id).toBe(42);
  });

  it("creates a pickup request with form data and reports upload progress", async () => {
    const progressSpy = vi.fn();
    const uploadProgress = (value: number) => progressSpy(value);

    server.use(
      http.post("*/pickup-requests", async ({ request }) => {
        const formData = await request.formData();
        return HttpResponse.json(
          createPickupRequestFixture({
            id: 9,
            waste_type: String(formData.get("waste_type")),
            address: String(formData.get("address")),
          }),
          { status: 201 },
        );
      }),
    );

    const created = await createPickupRequest(
      {
        waste_type: "  Metal cans ",
        address: " 5 New Lane ",
        latitude: 22.5,
        longitude: 88.3,
      },
      uploadProgress,
    );

    expect(created.id).toBe(9);
    expect(created.waste_type).toBe("Metal cans");
    expect(progressSpy).toHaveBeenCalled();
  });

  it("creates a pickup request without a progress callback", async () => {
    server.use(
      http.post("*/pickup-requests", () =>
        HttpResponse.json(createPickupRequestFixture({ id: 10 }), { status: 201 }),
      ),
    );

    const created = await createPickupRequest({
      waste_type: "Cardboard",
      address: "1 Main Street",
      latitude: 22.5,
      longitude: 88.3,
    });

    expect(created.id).toBe(10);
  });

  it("updates a pickup request", async () => {
    server.use(
      http.patch("*/pickup-requests/3", async ({ request }) => {
        const body = (await request.json()) as { address?: string };
        return HttpResponse.json(
          createPickupRequestFixture({ id: 3, address: body.address }),
        );
      }),
    );

    const updated = await updatePickupRequest(3, { address: "9 New Lane" });
    expect(updated.id).toBe(3);
    expect(updated.address).toBe("9 New Lane");
  });

  it("cancels a pickup request", async () => {
    server.use(
      http.post("*/pickup-requests/4/cancel", () =>
        HttpResponse.json(
          createPickupRequestFixture({ id: 4, status: "cancelled", can_cancel: false }),
        ),
      ),
    );

    const cancelled = await cancelPickupRequest(4);
    expect(cancelled.status).toBe("cancelled");
    expect(cancelled.can_cancel).toBe(false);
  });
});
