import { http, HttpResponse } from "msw";
import type { UserProfile } from "@/types/auth";
import {
  authResponseFor,
  createAdminAnalytics,
  createAdminDealer,
  createAdminUser,
  createCitizenSummary,
  createCollectorSummary,
  createDealerLotPage,
  createPickupRequest,
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

  http.get("*/collector/available", () => {
    return HttpResponse.json([
      createPickupRequest({
        id: 3,
        waste_type: "Cardboard",
        image_url: "https://example.com/img.jpg",
      }),
      createPickupRequest({ id: 4, waste_type: "Glass bottles" }),
    ]);
  }),

  http.get("*/dealer/inventory-lots", () => {
    return HttpResponse.json(createDealerLotPage());
  }),

  http.get("*/admin/analytics", () => {
    return HttpResponse.json(createAdminAnalytics());
  }),

  http.get("*/admin/users", () => {
    return HttpResponse.json([createAdminUser()]);
  }),

  http.get("*/admin/dealers", () => {
    return HttpResponse.json([createAdminDealer()]);
  }),
];
