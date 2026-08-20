import { http, HttpResponse } from "msw";
import type { UserProfile } from "@/types/auth";
import type { PickupRequest, PickupStatus } from "@/types/pickup";
import type { CollectorLocation } from "@/types/map";
import type { AppNotification } from "@/types/notification";
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
  createCollectorLocation as makeCollectorLocation,
  createCollectorMapPayload,
  createCollectorPerformance,
  createCollectorSummary,
  createDealerApprovalAction,
  createDealerApprovalEvent,
  createDealerLotPage,
  createDealerPerformance,
  createDealerProfile,
  createMarketplaceLot,
  createMarketplaceOrder,
  createMarketplaceOrderDetail,
  createMarketplaceTransaction,
  createMaterialBreakdown,
  createMonthlyAnalytics,
  createNavigation,
  createNearbyPickup,
  createNotification,
  createNotificationPage,
  createPickupRequest,
  createPickupRequestDetail,
  createRouteSummary,
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

// ─── Email verification store ────────────────────────────────────────────────

const verifiedUserIds = new Set<number>();

export function resetVerificationStore(): void {
  verifiedUserIds.clear();
}

export function profileForUser(user: UserProfile): UserProfile {
  return verifiedUserIds.has(user.id)
    ? {
        ...user,
        email_verified: true,
        email_verified_at: "2026-01-01T12:00:00Z",
      }
    : user;
}

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

// ─── Marketplace store ───────────────────────────────────────────────────────

function buildMarketplaceStore() {
  const now = new Date();
  const expiresAt = new Date(now.getTime() + 23 * 60 * 60 * 1000).toISOString();
  const reservedAt = new Date(now.getTime() - 60 * 60 * 1000).toISOString();

  return {
    lots: [
      createMarketplaceLot({
        id: 201,
        lot_number: "LOT-2026-000201",
        material_category_name: "PET Plastic",
        material_description: "Mixed PET bottles",
        weight_kg: 42.5,
        unit_price_per_kg_snapshot: 18.0,
        total_listed_amount: 765.0,
        source_city: "Kolkata",
        seller_name: "Test Citizen",
      }),
      createMarketplaceLot({
        id: 202,
        lot_number: "LOT-2026-000202",
        material_category_name: "Cardboard",
        material_description: "Cardboard boxes",
        weight_kg: 120.0,
        unit_price_per_kg_snapshot: 6.5,
        total_listed_amount: 780.0,
        source_city: "Howrah",
        seller_name: "Test Citizen",
      }),
      createMarketplaceLot({
        id: 203,
        lot_number: "LOT-2026-000203",
        material_category_name: "Glass",
        material_description: "Glass bottles",
        weight_kg: 25.0,
        unit_price_per_kg_snapshot: 4.0,
        total_listed_amount: 100.0,
        source_city: "Kolkata",
        seller_name: "Test Citizen",
        status: "reserved",
        is_reserved_by_me: true,
        reserved_at: reservedAt,
        reservation_expires_at: expiresAt,
      }),
      createMarketplaceLot({
        id: 204,
        lot_number: "LOT-2026-000204",
        material_category_name: "Metal",
        material_description: "Aluminum cans",
        weight_kg: 30.0,
        unit_price_per_kg_snapshot: 55.0,
        total_listed_amount: 1650.0,
        source_city: "Kolkata",
        seller_name: "Test Citizen",
        status: "sold",
        is_reserved_by_me: false,
      }),
    ],
    transactions: [
      createMarketplaceTransaction({
        id: 501,
        inventory_lot_id: 203,
        lot_number: "LOT-2026-000203",
        material_category_name: "Glass",
        quantity_kg: 25.0,
        total_amount: 100.0,
        transaction_type: "reservation",
        created_at: reservedAt,
      }),
      createMarketplaceTransaction({
        id: 502,
        inventory_lot_id: 204,
        lot_number: "LOT-2026-000204",
        material_category_name: "Metal",
        quantity_kg: 30.0,
        total_amount: 1650.0,
        transaction_type: "reservation",
        created_at: "2026-01-11T09:00:00Z",
      }),
      createMarketplaceTransaction({
        id: 503,
        order_id: 301,
        inventory_lot_id: 204,
        lot_number: "LOT-2026-000204",
        material_category_name: "Metal",
        quantity_kg: 30.0,
        total_amount: 1650.0,
        transaction_type: "purchase",
        status: "completed",
        created_at: "2026-01-11T09:30:00Z",
      }),
    ],
    orders: [
      createMarketplaceOrder({
        id: 301,
        order_number: "ORD-2026-000301",
        inventory_lot_id: 204,
        lot_number: "LOT-2026-000204",
        material_category_name: "Metal",
        material_description: "Aluminum cans",
        quantity_kg: 30.0,
        total_amount: 1650.0,
        created_at: "2026-01-11T09:30:00Z",
        updated_at: "2026-01-11T09:30:00Z",
      }),
    ],
  };
}

export let marketplaceStore = buildMarketplaceStore();

export function resetMarketplaceStore(): void {
  marketplaceStore = buildMarketplaceStore();
}

// ─── Notification store ──────────────────────────────────────────────────────

export function buildNotificationStore(): AppNotification[] {
  return [
    createNotification({
      id: 701,
      user_id: 1,
      title: "Pickup request created",
      message: "Your pickup request for Cardboard was created.",
      type: "pickup_created",
      link: "/dashboard/pickups/3",
      created_at: "2026-01-05T09:00:00Z",
    }),
    createNotification({
      id: 702,
      user_id: 1,
      title: "Pickup accepted",
      message: "Test Collector accepted your pickup request.",
      type: "pickup_accepted",
      link: "/dashboard/pickups/5",
      created_at: "2026-01-04T10:30:00Z",
    }),
    createNotification({
      id: 703,
      user_id: 1,
      title: "Pickup completed",
      message: "Your pickup request was completed. Weight collected: 12.5 kg.",
      type: "pickup_completed",
      status: "read",
      link: "/dashboard/pickups/2",
      read_at: "2026-01-03T11:00:00Z",
      created_at: "2026-01-03T10:00:00Z",
    }),
    createNotification({
      id: 704,
      user_id: 4,
      title: "New dealer profile submitted",
      message: "Green Scrap Co submitted a dealer profile for approval.",
      type: "dealer_profile_submitted",
      link: "/admin/dealers/3",
      created_at: "2026-01-05T08:00:00Z",
    }),
    createNotification({
      id: 705,
      user_id: 3,
      title: "Inventory lot listed",
      message: "Your inventory lot LOT-2026-000201 is now listed on the marketplace.",
      type: "inventory_created",
      link: "/dealer/marketplace/201",
      created_at: "2026-01-05T07:00:00Z",
    }),
  ];
}

export let notificationStore: AppNotification[] = buildNotificationStore();

export function resetNotificationStore(): void {
  notificationStore = buildNotificationStore();
}

function requireDealer(request: Request): boolean {
  return requireAuthorization(request)?.role === "dealer";
}

function marketplaceLotById(lotId: number) {
  return marketplaceStore.lots.find((lot) => lot.id === lotId);
}

function nextTransactionId(): number {
  return Math.max(...marketplaceStore.transactions.map((transaction) => transaction.id)) + 1;
}

function nextOrderId(): number {
  return Math.max(...marketplaceStore.orders.map((order) => order.id)) + 1;
}

function paginate<T>(items: T[], page: number, pageSize: number): { items: T[]; totalItems: number } {
  const totalItems = items.length;
  const start = (page - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    totalItems,
  };
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
) {
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

export let collectorLocationStore: CollectorLocation = makeCollectorLocation();

export function resetCollectorMapStore(): void {
  collectorLocationStore = makeCollectorLocation();
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

  http.post("*/auth/refresh", async ({ request }) => {
    const body = (await request.json()) as { refresh_token?: string };

    if (!body.refresh_token || body.refresh_token === "revoked-refresh-token") {
      return HttpResponse.json({ detail: "Invalid refresh token" }, { status: 401 });
    }

    return HttpResponse.json(authResponseFor(BASE_USER));
  }),

  http.post("*/auth/logout", () => new HttpResponse(null, { status: 204 })),

  http.post("*/auth/logout-all", () => new HttpResponse(null, { status: 204 })),

  http.get("*/auth/me", ({ request }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    return HttpResponse.json(profileForUser(user));
  }),

  http.post("*/auth/verify-email", async ({ request }) => {
    const body = (await request.json()) as { token?: string };
    const match = /^verification-token-(\d+)$/.exec(body.token ?? "");

    if (!match) {
      return HttpResponse.json(
        { detail: "Invalid or expired verification token" },
        { status: 400 },
      );
    }

    const userId = Number(match[1]);

    if (!USER_BY_ID[userId]) {
      return HttpResponse.json(
        { detail: "Invalid or expired verification token" },
        { status: 400 },
      );
    }

    if (verifiedUserIds.has(userId)) {
      return HttpResponse.json({ message: "Email already verified" });
    }

    verifiedUserIds.add(userId);
    return HttpResponse.json({ message: "Email verified successfully" });
  }),

  http.post("*/auth/resend-verification", async ({ request }) => {
    const body = (await request.json()) as { email?: string };

    if (body.email === "rate-limited@example.com") {
      return HttpResponse.json(
        { detail: "Rate limit exceeded" },
        { status: 429, headers: { "Retry-After": "300" } },
      );
    }

    return HttpResponse.json({
      message: "If the email is registered and unverified, a verification email has been sent.",
    });
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

  http.get("*/pickup-requests/:id", ({ request, params }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const pickup = pickupStore.find((candidate) => candidate.id === Number(params.id));

    if (!pickup) {
      return HttpResponse.json({ detail: "Pickup request not found" }, { status: 404 });
    }

    return HttpResponse.json(createPickupRequestDetail(pickup));
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

  // ─── Collector live map & route tracking ──────────────────────────────────

  http.get("*/collector/map", ({ request }) => {
    if (!requireCollector(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const url = new URL(request.url);
    const radiusKm = Number(url.searchParams.get("radius_km") ?? 5);
    return HttpResponse.json(
      createCollectorMapPayload({ collector: collectorLocationStore, radius_km: radiusKm }),
    );
  }),

  http.get("*/collector/location", ({ request }) => {
    if (!requireCollector(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    return HttpResponse.json(collectorLocationStore);
  }),

  http.post("*/collector/location", async ({ request }) => {
    if (!requireCollector(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const body = (await request.json()) as {
      latitude?: number;
      longitude?: number;
      accuracy?: number | null;
    };

    if (typeof body.latitude !== "number" || typeof body.longitude !== "number") {
      return HttpResponse.json({ detail: "latitude and longitude are required" }, { status: 422 });
    }

    collectorLocationStore = {
      latitude: body.latitude,
      longitude: body.longitude,
      accuracy: body.accuracy ?? null,
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(collectorLocationStore);
  }),

  http.get("*/collector/route", ({ request }) => {
    if (!requireCollector(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    return HttpResponse.json(createRouteSummary());
  }),

  http.get("*/collector/nearby-pickups", ({ request }) => {
    if (!requireCollector(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    return HttpResponse.json([
      createNearbyPickup(),
      createNearbyPickup({
        id: 4,
        waste_type: "Glass bottles",
        address: "88 Park Avenue, Kolkata",
        distance_km: 2.3,
      }),
    ]);
  }),

  http.get("*/collector/navigation/:id", ({ request }) => {
    if (!requireCollector(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    return HttpResponse.json(createNavigation());
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

  // ─── Marketplace ───────────────────────────────────────────────────────────

  http.get("*/marketplace/inventory", ({ request }) => {
    if (!requireDealer(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const pageSize = Number(url.searchParams.get("page_size") ?? 12);
    const sortBy = url.searchParams.get("sort_by") ?? "created_at";
    const sortOrder = url.searchParams.get("sort_order") ?? "desc";
    const categoryId = url.searchParams.get("material_category_id");
    const city = url.searchParams.get("city")?.toLowerCase();
    const search = url.searchParams.get("search")?.toLowerCase();

    let lots = marketplaceStore.lots.filter(
      (lot) =>
        lot.status !== "sold" &&
        (lot.status === "available" || lot.is_reserved_by_me),
    );

    if (categoryId) {
      lots = lots.filter((lot) => lot.material_category_id === Number(categoryId));
    }
    if (city) {
      lots = lots.filter((lot) => lot.source_city.toLowerCase().includes(city));
    }
    if (search) {
      lots = lots.filter(
        (lot) =>
          lot.material_description?.toLowerCase().includes(search) ||
          lot.material_category_name.toLowerCase().includes(search),
      );
    }

    lots = [...lots].sort((a, b) => {
      const valueA = a[sortBy as keyof typeof a];
      const valueB = b[sortBy as keyof typeof b];
      if (typeof valueA === "string" && typeof valueB === "string") {
        return sortOrder === "asc" ? valueA.localeCompare(valueB) : valueB.localeCompare(valueA);
      }
      const numericA = Number(valueA ?? 0);
      const numericB = Number(valueB ?? 0);
      return sortOrder === "asc" ? numericA - numericB : numericB - numericA;
    });

    const { items, totalItems } = paginate(lots, page, pageSize);
    return HttpResponse.json({
      items,
      page,
      page_size: pageSize,
      total_items: totalItems,
      total_pages: Math.ceil(totalItems / pageSize),
    });
  }),

  http.get("*/marketplace/inventory/:id", ({ request, params }) => {
    if (!requireDealer(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const lot = marketplaceLotById(Number(params.id));

    if (!lot || lot.status === "sold" || (lot.status === "reserved" && !lot.is_reserved_by_me)) {
      return HttpResponse.json({ detail: "Inventory lot not found" }, { status: 404 });
    }

    return HttpResponse.json(lot);
  }),

  http.post("*/marketplace/inventory/:id/reserve", ({ request, params }) => {
    if (!requireDealer(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const lot = marketplaceLotById(Number(params.id));

    if (!lot) {
      return HttpResponse.json({ detail: "Inventory lot not found" }, { status: 404 });
    }
    if (lot.status === "reserved") {
      return HttpResponse.json({ detail: "Inventory lot is already reserved" }, { status: 409 });
    }
    if (lot.status === "sold") {
      return HttpResponse.json({ detail: "Inventory lot is already sold" }, { status: 409 });
    }

    const now = new Date();
    lot.status = "reserved";
    lot.is_reserved_by_me = true;
    lot.reserved_at = now.toISOString();
    lot.reservation_expires_at = new Date(now.getTime() + 24 * 60 * 60 * 1000).toISOString();
    marketplaceStore.transactions.push(
      createMarketplaceTransaction({
        id: nextTransactionId(),
        inventory_lot_id: lot.id,
        lot_number: lot.lot_number,
        material_category_name: lot.material_category_name,
        quantity_kg: lot.weight_kg,
        total_amount: lot.total_listed_amount,
        transaction_type: "reservation",
        status: "completed",
        created_at: lot.reserved_at,
      }),
    );

    return HttpResponse.json(lot);
  }),

  http.post("*/marketplace/inventory/:id/cancel-reservation", ({ request, params }) => {
    if (!requireDealer(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const lot = marketplaceLotById(Number(params.id));

    if (!lot) {
      return HttpResponse.json({ detail: "Inventory lot not found" }, { status: 404 });
    }
    if (lot.status !== "reserved") {
      return HttpResponse.json(
        { detail: "Inventory lot is not currently reserved" },
        { status: 400 },
      );
    }
    if (!lot.is_reserved_by_me) {
      return HttpResponse.json(
        { detail: "Reservation is held by another dealer" },
        { status: 409 },
      );
    }

    lot.status = "available";
    lot.is_reserved_by_me = false;
    lot.reserved_at = null;
    lot.reservation_expires_at = null;
    marketplaceStore.transactions.push(
      createMarketplaceTransaction({
        id: nextTransactionId(),
        inventory_lot_id: lot.id,
        lot_number: lot.lot_number,
        material_category_name: lot.material_category_name,
        quantity_kg: lot.weight_kg,
        total_amount: lot.total_listed_amount,
        transaction_type: "cancellation",
        status: "cancelled",
        created_at: new Date().toISOString(),
      }),
    );

    return HttpResponse.json(lot);
  }),

  http.post("*/marketplace/inventory/:id/purchase", ({ request, params }) => {
    if (!requireDealer(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const lot = marketplaceLotById(Number(params.id));

    if (!lot) {
      return HttpResponse.json({ detail: "Inventory lot not found" }, { status: 404 });
    }
    if (lot.status === "sold") {
      return HttpResponse.json({ detail: "Inventory lot is already sold" }, { status: 409 });
    }
    if (lot.status !== "reserved") {
      return HttpResponse.json(
        { detail: "Inventory lot must be reserved before it can be purchased" },
        { status: 400 },
      );
    }
    if (!lot.is_reserved_by_me) {
      return HttpResponse.json(
        { detail: "Inventory lot is reserved by another dealer" },
        { status: 409 },
      );
    }

    const order = createMarketplaceOrder({
      id: nextOrderId(),
      order_number: `ORD-2026-000${String(nextOrderId()).padStart(3, "0")}`,
      inventory_lot_id: lot.id,
      lot_number: lot.lot_number,
      material_category_id: lot.material_category_id,
      material_category_name: lot.material_category_name,
      material_description: lot.material_description,
      quantity_kg: lot.weight_kg,
      unit_price_per_kg_snapshot: lot.unit_price_per_kg_snapshot,
      total_amount: lot.total_listed_amount,
      currency_code: lot.currency_code ?? "INR",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
    marketplaceStore.orders.push(order);

    const purchaseTransaction = createMarketplaceTransaction({
      id: nextTransactionId(),
      order_id: order.id,
      inventory_lot_id: lot.id,
      lot_number: lot.lot_number,
      material_category_name: lot.material_category_name,
      quantity_kg: lot.weight_kg,
      total_amount: lot.total_listed_amount,
      transaction_type: "purchase",
      status: "completed",
      created_at: order.created_at,
    });
    marketplaceStore.transactions.push(purchaseTransaction);

    lot.status = "sold";
    lot.is_reserved_by_me = false;
    lot.reserved_at = null;
    lot.reservation_expires_at = null;

    const detail = createMarketplaceOrderDetail({
      ...order,
      transactions: marketplaceStore.transactions.filter(
        (transaction) => transaction.inventory_lot_id === lot.id,
      ),
    });

    return HttpResponse.json(detail, { status: 201 });
  }),

  http.get("*/marketplace/orders", ({ request }) => {
    if (!requireDealer(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const pageSize = Number(url.searchParams.get("page_size") ?? 20);
    const sorted = [...marketplaceStore.orders].sort((a, b) =>
      b.created_at.localeCompare(a.created_at),
    );
    const { items, totalItems } = paginate(sorted, page, pageSize);
    return HttpResponse.json({
      items,
      page,
      page_size: pageSize,
      total_items: totalItems,
      total_pages: Math.ceil(totalItems / pageSize),
    });
  }),

  http.get("*/marketplace/orders/:id", ({ request, params }) => {
    if (!requireDealer(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const order = marketplaceStore.orders.find((candidate) => candidate.id === Number(params.id));

    if (!order) {
      return HttpResponse.json({ detail: "Order not found" }, { status: 404 });
    }

    return HttpResponse.json(
      createMarketplaceOrderDetail({
        ...order,
        transactions: marketplaceStore.transactions.filter(
          (transaction) => transaction.inventory_lot_id === order.inventory_lot_id,
        ),
      }),
    );
  }),

  http.get("*/marketplace/transactions", ({ request }) => {
    if (!requireDealer(request)) {
      return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
    }

    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const pageSize = Number(url.searchParams.get("page_size") ?? 20);
    const transactionType = url.searchParams.get("transaction_type");

    let transactions = [...marketplaceStore.transactions].sort((a, b) =>
      b.created_at.localeCompare(a.created_at),
    );
    if (transactionType) {
      transactions = transactions.filter(
        (transaction) => transaction.transaction_type === transactionType,
      );
    }

    const { items, totalItems } = paginate(transactions, page, pageSize);
    return HttpResponse.json({
      items,
      page,
      page_size: pageSize,
      total_items: totalItems,
      total_pages: Math.ceil(totalItems / pageSize),
    });
  }),

  // ─── Notifications ─────────────────────────────────────────────────────────

  http.get("*/notifications/unread/count", ({ request }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const unreadCount = notificationStore.filter(
      (notification) => notification.user_id === user.id && notification.status === "unread",
    ).length;
    return HttpResponse.json({ unread_count: unreadCount });
  }),

  http.get("*/notifications/unread", ({ request }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    return HttpResponse.json(
      notificationStore
        .filter(
          (notification) => notification.user_id === user.id && notification.status === "unread",
        )
        .sort((a, b) => b.created_at.localeCompare(a.created_at)),
    );
  }),

  http.get("*/notifications", ({ request }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const pageSize = Number(url.searchParams.get("page_size") ?? 20);
    const status = url.searchParams.get("status");

    let notifications = notificationStore.filter(
      (notification) => notification.user_id === user.id,
    );
    if (status === "unread" || status === "read") {
      notifications = notifications.filter((notification) => notification.status === status);
    }
    notifications = [...notifications].sort((a, b) => b.created_at.localeCompare(a.created_at));

    const { items, totalItems } = paginate(notifications, page, pageSize);
    return HttpResponse.json(
      createNotificationPage(items, {
        page,
        page_size: pageSize,
        total_items: totalItems,
        total_pages: Math.ceil(totalItems / pageSize),
      }),
    );
  }),

  http.get("*/notifications/:id", ({ request, params }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const notification = notificationStore.find(
      (candidate) => candidate.id === Number(params.id) && candidate.user_id === user.id,
    );

    if (!notification) {
      return HttpResponse.json({ detail: "Notification not found" }, { status: 404 });
    }

    return HttpResponse.json(notification);
  }),

  http.post("*/notifications/:id/read", ({ request, params }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const notification = notificationStore.find(
      (candidate) => candidate.id === Number(params.id) && candidate.user_id === user.id,
    );

    if (!notification) {
      return HttpResponse.json({ detail: "Notification not found" }, { status: 404 });
    }

    if (notification.status === "unread") {
      notification.status = "read";
      notification.read_at = new Date().toISOString();
    }

    return HttpResponse.json(notification);
  }),

  http.post("*/notifications/read-all", ({ request }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    let affected = 0;
    for (const notification of notificationStore) {
      if (notification.user_id === user.id && notification.status === "unread") {
        notification.status = "read";
        notification.read_at = new Date().toISOString();
        affected += 1;
      }
    }

    return HttpResponse.json({ affected });
  }),

  http.delete("*/notifications/read", ({ request }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const readNotifications = notificationStore.filter(
      (notification) => notification.user_id === user.id && notification.status === "read",
    );
    notificationStore = notificationStore.filter(
      (notification) =>
        !(notification.user_id === user.id && notification.status === "read"),
    );

    return HttpResponse.json({ affected: readNotifications.length });
  }),

  http.delete("*/notifications/:id", ({ request, params }) => {
    const user = requireAuthorization(request);

    if (!user) {
      return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const index = notificationStore.findIndex(
      (candidate) => candidate.id === Number(params.id) && candidate.user_id === user.id,
    );

    if (index === -1) {
      return HttpResponse.json({ detail: "Notification not found" }, { status: 404 });
    }

    notificationStore.splice(index, 1);
    return new HttpResponse(null, { status: 204 });
  }),
];
