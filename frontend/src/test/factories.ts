import type { UserProfile, UserRole } from "@/types/auth";
import type { AdminAnalytics, AdminDealerSummary, AdminUser } from "@/types/admin";
import type { DealerInventoryLot, DealerInventoryLotPage } from "@/types/inventory";
import type { CitizenRequestSummary, PickupRequest } from "@/types/pickup";
import type { CollectorSummary } from "@/types/collector";

export interface TestTokenOptions {
  sub?: string;
  exp?: number;
  iat?: number;
}

function encodeSegment(value: unknown): string {
  const json = JSON.stringify(value);
  const base64 = typeof window !== "undefined" ? window.btoa(json) : Buffer.from(json).toString("base64");
  return base64.replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
}

export function createTestToken(options: TestTokenOptions = {}): string {
  const nowSeconds = Math.floor(Date.now() / 1000);
  const payload = {
    sub: options.sub ?? "1",
    iat: options.iat ?? nowSeconds - 60,
    exp: options.exp ?? nowSeconds + 3600,
  };
  return `${encodeSegment({ alg: "HS256", typ: "JWT" })}.${encodeSegment(payload)}.fake-signature`;
}

export const EXPIRED_TOKEN = createTestToken({ exp: Math.floor(Date.now() / 1000) - 3600 });
export const MALFORMED_TOKEN = "not-a-real-jwt-token";
export const VALID_TOKEN = createTestToken();

export function createUser(overrides: Partial<UserProfile> = {}): UserProfile {
  return {
    id: 1,
    name: "Test Citizen",
    email: "citizen@example.com",
    phone: "+15550000000",
    role: "citizen",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

export const usersByRole: Record<UserRole, UserProfile> = {
  citizen: createUser({ id: 1, name: "Test Citizen", email: "citizen@example.com", role: "citizen" }),
  collector: createUser({ id: 2, name: "Test Collector", email: "collector@example.com", role: "collector" }),
  dealer: createUser({ id: 3, name: "Test Dealer", email: "dealer@example.com", role: "dealer" }),
  admin: createUser({ id: 4, name: "Test Admin", email: "admin@example.com", role: "admin" }),
};

export function authResponseFor(user: UserProfile) {
  return {
    access_token: createTestToken({ sub: String(user.id) }),
    token_type: "bearer" as const,
    user,
  };
}

export function createPickupRequest(overrides: Partial<PickupRequest> = {}): PickupRequest {
  return {
    id: 1,
    user_id: 1,
    citizen_name: "Test Citizen",
    citizen_phone: "+15550000000",
    waste_type: "Plastic bottles",
    category: null,
    confidence: null,
    image_url: null,
    address: "12 Green Street, Kolkata",
    latitude: 22.5726,
    longitude: 88.3639,
    estimated_weight_kg: null,
    preferred_time: null,
    notes: null,
    status: "pending",
    created_at: "2026-01-10T08:00:00Z",
    assigned_collector_name: null,
    can_cancel: true,
    assignment: null,
    ...overrides,
  };
}

export function createCitizenSummary(overrides: Partial<CitizenRequestSummary> = {}): CitizenRequestSummary {
  return {
    total_requests: 5,
    pending_requests: 2,
    accepted_requests: 1,
    completed_requests: 2,
    ...overrides,
  };
}

export function createCollectorSummary(overrides: Partial<CollectorSummary> = {}): CollectorSummary {
  return {
    total_assigned: 10,
    active_jobs: 3,
    completed_jobs: 7,
    total_weight_kg: 125.5,
    ...overrides,
  };
}

export function createDealerLot(overrides: Partial<DealerInventoryLot> = {}): DealerInventoryLot {
  return {
    id: 101,
    material_category_id: 1,
    material_category_name: "Plastic",
    material_description: "Mixed PET bottles",
    weight_kg: 42.5,
    unit_price_per_kg_snapshot: 18.0,
    total_listed_amount: 765.0,
    source_city: "Kolkata",
    status: "available",
    created_at: "2026-01-12T10:00:00Z",
    ...overrides,
  };
}

export function createDealerLotPage(overrides: Partial<DealerInventoryLotPage> = {}): DealerInventoryLotPage {
  return {
    items: [createDealerLot()],
    page: 1,
    page_size: 12,
    total_items: 1,
    total_pages: 1,
    ...overrides,
  };
}

export function createAdminAnalytics(overrides: Partial<AdminAnalytics> = {}): AdminAnalytics {
  return {
    total_users: 42,
    total_pickup_requests: 150,
    total_completed_pickups: 60,
    total_collected_weight_kg: 1200.75,
    users_by_role: { citizens: 30, collectors: 8, dealers: 3, admins: 1 },
    requests_by_status: {
      pending: 40,
      accepted: 20,
      on_the_way: 10,
      collected: 15,
      completed: 60,
      cancelled: 5,
    },
    ...overrides,
  };
}

export function createAdminUser(overrides: Partial<AdminUser> = {}): AdminUser {
  return {
    id: 1,
    name: "Test Citizen",
    email: "citizen@example.com",
    phone: "+15550000000",
    role: "citizen",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

export function createAdminDealer(overrides: Partial<AdminDealerSummary> = {}): AdminDealerSummary {
  return {
    user_id: 3,
    user_name: "Test Dealer",
    user_email: "dealer@example.com",
    account_phone: "+15550000003",
    has_profile: true,
    business_name: "Green Scrap Co",
    owner_name: "Test Dealer",
    city: "Kolkata",
    pincode: "700001",
    materials_accepted: ["plastic", "paper"],
    verification_status: "pending",
    approved_at: null,
    profile_completion: 80,
    created_at: "2026-01-05T00:00:00Z",
    ...overrides,
  };
}
