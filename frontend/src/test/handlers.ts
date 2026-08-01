import { http, HttpResponse } from "msw";
import type { UserProfile } from "@/types/auth";
import type { PickupRequest, PickupStatus } from "@/types/pickup";
import {
  authResponseFor,
  createAdminAnalytics,
  createAdminDealer,
  createAdminDealerListPage,
  createAdminUser,
  createAnalyticsInsights,
  createAnalyticsOverview,
  createCarbonSavings,
  createCitizenSummary,
  createCollectorPerformance,
  createCollectorSummary,
  createDealerApprovalAction,
  createDealerApprovalEvent,
  createDealerLotPage,
  createDealerPerformance,
  createDealerProfile,
  createMaterialBreakdown,
  createMonthlyAnalytics,
  createPickupRequest,
  createPickupRequestDetail,
  createUser,
  usersByRole,
} from "./factories";

const BASE_USER: UserProfile = createUser();

const USER_BY_ID: Record<number, UserProfile> = {
  1: usersByRole.citizen,
  2: usersByRole.collector,
  3: usersByRole.dealer,
  4: usersByRole.admin,
};

function decodeTokenSubject(token: string | null): number | null {
  if (!token) {
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
    const payload = JSON.parse(window.atob(base64)) as { sub?: string };
    const subject = Number(payload.sub);

    return Number.isFinite(subject) ? subject : null;
  } catch {
    return null;
  }
}

function requireAuthorization(request: Request): UserProfile | null {
  const header = request.headers.get("authorization");

  if (!header?.startsWith("Bearer ")) {
    return null;
  }

  const subject = decodeTokenSubject(header.slice("Bearer ".length));

  return subject !== null ? (USER_BY_ID[subject] ?? null) : null;
}

const COLLECTOR_ID = usersByRole.collector.id;

function buildPickupStore(): PickupRequest[] {
  return [
    createPickupRequest({
      id: 3,
      waste_type: "Cardboard",
      image_url: "https://example.com/img.jpg",
    }),
    createPickupRequest({ id: 4, waste_type: "Glass bottles" }),
    createPickupRequest({
      id: 5,
      waste_type: "Paper",
      status: "accepted",
      can_cancel: false,
      assigned_collector_name: "Test Collector",
      assignment: {
        id: 5,
        collector_id: COLLECTOR_ID,
        collector_name: "Test Collector",
        accepted_at: "2026-01-10T09:00:00Z",
        completed_at: null,
        weight_kg: null,
      },
    }),
  ];
}

export let pickupStore: PickupRequest[] = buildPickupStore();

export function resetPickupStore(): void {
  pickupStore = buildPickupStore();
}

function requireCollector(request: Request): boolean {
  return requireAuthorization(request)?.role === "collector";
}

function pickupById(requestId: number): PickupRequest | undefined {
  return pickupStore.find((request) => request.id === requestId);
}

function applyTransition(
  request: Request,
  requestId: number,
  status: PickupStatus,
  patch: Partial<PickupRequest> = {},
): HttpResponse<any> {
  if (!requireCollector(request)) {
    return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
  }

  const pickup = pickupById(requestId);

  if (!pickup) {
    return HttpResponse.json({ detail: "Pickup request not found" }, { status: 404 });
  }

  Object.assign(pickup, { status, ...patch });
  return HttpResponse.json(pickup);
}

export const handlers = [
  http.post("*/auth/login", async ({ request }) => {
    const body = (await request.json()) as { email?: string; password?: string };
    const email = body.email ?? "";
    const user = Object.values(usersByRole).find((candidate) => candidate.email === email);

    if (!user || body.password !== "correct-password") {
      return HttpResponse.json(
        { detail: "Invalid email or password" },
        { status: 401 },
      );
    }

    return HttpResponse.json(authResponseFor(user));
  }),

  http.post("*/auth/register", async ({ request }) => {
    const body = (await request.json()) as {
      email?: string;
      name?: string;
      phone?: string;
      password?: string;
    };

    if (!body.email || !body.name || !body.phone || !body.password) {
      return HttpResponse.json({ detail: "Registration failed" }, { status: 400 });
    }

    return HttpResponse.json(authResponseFor(BASE_USER), { status: 201 });
  }),

  http.get("*/auth/me", ({ request }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    return HttpResponse.json(user);
  }),

  http.get("*/pickup-requests", () => {
    return HttpResponse.json([
      createPickupRequest({ id: 1, status: "pending" }),
      createPickupRequest({
        id: 2,
        status: "completed",
        can_cancel: false,
        waste_type: "Cardboard",
        assignment: {
          id: 2,
          collector_id: 2,
          collector_name: "Test Collector",
          accepted_at: "2026-01-10T09:00:00Z",
          completed_at: "2026-01-10T10:00:00Z",
          weight_kg: 12.5,
        },
      }),
    ]);
  }),

  http.post("*/pickup-requests", async ({ request }) => {
    const formData = await request.formData();
    const wasteType = String(formData.get("waste_type") ?? "");
    const address = String(formData.get("address") ?? "");
    const latitude = Number(formData.get("latitude") ?? 0);
    const longitude = Number(formData.get("longitude") ?? 0);
    const rawWeight = formData.get("estimated_weight_kg");
    const estimatedWeightKg =
      rawWeight !== null && rawWeight !== "" ? Number(rawWeight) : null;
    const preferredTime = formData.get("preferred_time") as string | null;
    const notes = formData.get("notes") as string | null;
    const image = formData.get("image") as File | null;

    return HttpResponse.json(
      createPickupRequest({
        id: 101,
        waste_type: wasteType,
        address,
        latitude,
        longitude,
        estimated_weight_kg: estimatedWeightKg,
        preferred_time: preferredTime,
        notes,
        image_url: image ? "https://example.com/uploads/test.jpg" : null,
        category: image ? "Unknown" : null,
        confidence: image ? 0 : null,
      }),
      { status: 201 },
    );
  }),

  http.get("*/pickup-requests/citizen/summary", () => {
    return HttpResponse.json(createCitizenSummary());
  }),

  http.get("*/collector/summary", () => {
    return HttpResponse.json(createCollectorSummary());
  }),

  http.get("*/collector/pickups/available", ({ request }) => {
    if (!requireCollector(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    return HttpResponse.json(
      pickupStore.filter((pickup) => pickup.status === "pending"),
    );
  }),

  http.get("*/collector/pickups/assigned", ({ request }) => {
    if (!requireCollector(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    return HttpResponse.json(
      pickupStore.filter(
        (pickup) =>
          pickup.status !== "pending" && pickup.status !== "cancelled",
      ),
    );
  }),

  http.get("*/collector/pickups/:id", ({ params }) => {
    const pickup = pickupById(Number(params.id));

    if (!pickup) {
      return HttpResponse.json({ detail: "Pickup request not found" }, { status: 404 });
    }

    return HttpResponse.json(createPickupRequestDetail(pickup));
  }),

  http.post("*/collector/pickups/:id/accept", ({ request, params }) => {
    const pickup = pickupById(Number(params.id));

    if (!pickup || pickup.status !== "pending") {
      return HttpResponse.json({ detail: "Pickup request is no longer available" }, { status: 400 });
    }

    return applyTransition(request, pickup.id, "accepted", {
      can_cancel: false,
      assigned_collector_name: "Test Collector",
      assignment: {
        id: pickup.id,
        collector_id: COLLECTOR_ID,
        collector_name: "Test Collector",
        accepted_at: "2026-01-10T09:00:00Z",
        completed_at: null,
        weight_kg: null,
      },
    });
  }),

  http.post("*/collector/pickups/:id/start", ({ request, params }) => {
    const pickup = pickupById(Number(params.id));

    if (!pickup || pickup.status !== "accepted") {
      return HttpResponse.json({ detail: "Only accepted requests can be started" }, { status: 400 });
    }

    return applyTransition(request, pickup.id, "on_the_way");
  }),

  http.post("*/collector/pickups/:id/collect", ({ request, params }) => {
    const pickup = pickupById(Number(params.id));

    if (!pickup || pickup.status !== "on_the_way") {
      return HttpResponse.json({ detail: "Only in-progress requests can be collected" }, { status: 400 });
    }

    return applyTransition(request, pickup.id, "collected");
  }),

  http.post("*/collector/pickups/:id/complete", async ({ request, params }) => {
    const pickup = pickupById(Number(params.id));

    if (!pickup || pickup.status !== "collected") {
      return HttpResponse.json({ detail: "Only collected requests can be completed" }, { status: 400 });
    }

    const body = (await request.json()) as { weight_kg?: number };
    const weightKg = body.weight_kg ?? 0;

    if (weightKg <= 0) {
      return HttpResponse.json(
        { detail: [{ msg: "Value error, weight_kg must be greater than 0" }] },
        { status: 422 },
      );
    }

    return applyTransition(request, pickup.id, "completed", {
      can_cancel: false,
      assignment: pickup.assignment
        ? {
            ...pickup.assignment,
            completed_at: "2026-01-10T10:00:00Z",
            weight_kg: weightKg,
          }
        : pickup.assignment,
    });
  }),

  http.post("*/collector/pickups/:id/cancel", ({ request, params }) => {
    const pickup = pickupById(Number(params.id));

    if (!pickup || pickup.status !== "accepted") {
      return HttpResponse.json(
        { detail: "Only accepted requests can be cancelled" },
        { status: 400 },
      );
    }

    return applyTransition(request, pickup.id, "pending", {
      can_cancel: true,
      assigned_collector_name: null,
      assignment: null,
    });
  }),

  http.get("*/dealer/inventory-lots", () => {
    return HttpResponse.json(createDealerLotPage());
  }),

  http.get("*/dealer/profile", () => {
    return HttpResponse.json(createDealerProfile());
  }),

  http.get("*/dealer/profile/timeline", () => {
    return HttpResponse.json([
      createDealerApprovalEvent({
        id: 2,
        status: "approved",
        note: "Profile approved by administrator.",
        actor_name: "Test Admin",
        actor_role: "admin",
        created_at: "2026-01-06T09:00:00Z",
      }),
      createDealerApprovalEvent(),
    ]);
  }),

  http.post("*/dealer/profile/submit", () => {
    return HttpResponse.json(
      createDealerProfile({ approval_status: "submitted", is_verified: false, approved_at: null }),
    );
  }),

  http.post("*/dealer/profile", () => {
    return HttpResponse.json(
      createDealerProfile({ approval_status: "draft", is_verified: false, approved_at: null }),
      { status: 201 },
    );
  }),

  http.put("*/dealer/profile", () => {
    return HttpResponse.json(
      createDealerProfile({ approval_status: "draft", is_verified: false, approved_at: null }),
    );
  }),

  http.get("*/admin/analytics", () => {
    return HttpResponse.json(createAdminAnalytics());
  }),

  http.get("*/admin/analytics/overview", () => {
    return HttpResponse.json(createAnalyticsOverview());
  }),

  http.get("*/admin/analytics/materials", () => {
    return HttpResponse.json(createMaterialBreakdown());
  }),

  http.get("*/admin/analytics/monthly", () => {
    return HttpResponse.json(createMonthlyAnalytics());
  }),

  http.get("*/admin/analytics/collectors", () => {
    return HttpResponse.json(createCollectorPerformance());
  }),

  http.get("*/admin/analytics/dealers", () => {
    return HttpResponse.json(createDealerPerformance());
  }),

  http.get("*/admin/analytics/carbon", () => {
    return HttpResponse.json(createCarbonSavings());
  }),

  http.get("*/admin/analytics/insights", () => {
    return HttpResponse.json(createAnalyticsInsights());
  }),

  http.get("*/admin/users", () => {
    return HttpResponse.json([createAdminUser()]);
  }),

  http.get("*/admin/dealers", () => {
    return HttpResponse.json(createAdminDealerListPage());
  }),

  http.get("*/admin/dealers/pending", () => {
    return HttpResponse.json(createAdminDealerListPage());
  }),

  http.post("*/admin/dealers/:id/approve", ({ params }) => {
    const dealer = createAdminDealer({ user_id: Number(params.id) });
    return HttpResponse.json(
      createDealerApprovalAction({
        user_id: dealer.user_id,
        profile_id: dealer.user_id,
      }),
    );
  }),

  http.post("*/admin/dealers/:id/reject", async ({ request, params }) => {
    const body = (await request.json()) as { reason?: string };
    const dealer = createAdminDealer({ user_id: Number(params.id) });
    return HttpResponse.json(
      createDealerApprovalAction({
        user_id: dealer.user_id,
        profile_id: dealer.user_id,
        approval_status: "rejected",
        is_verified: false,
        approved_at: null,
        rejection_reason: body.reason ?? "No reason provided",
      }),
    );
  }),
];
