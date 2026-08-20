import type { UserProfile, UserRole } from "@/types/auth";
import type {
  AdminAnalytics,
  AdminDealerListPage,
  AdminDealerSummary,
  AdminUser,
} from "@/types/admin";
import type {
  DealerApprovalAction,
  DealerApprovalEvent,
  DealerApprovalStatus,
  DealerProfile,
} from "@/types/dealer";
import type {
  AnalyticsInsight,
  AnalyticsOverview,
  CarbonSavings,
  CollectorPerformance,
  DealerPerformance,
  MaterialBreakdown,
  MonthlyStat,
} from "@/types/analytics";
import type { DealerInventoryLot, DealerInventoryLotPage } from "@/types/inventory";
import type {
  MarketplaceInventoryLot,
  MarketplaceInventoryPage,
  MarketplaceOrder,
  MarketplaceOrderDetail,
  MarketplaceOrderPage,
  MarketplaceTransaction,
  MarketplaceTransactionPage,
  MarketplaceTransactionType,
} from "@/types/marketplace";
import type { CitizenRequestSummary, PickupRequest, PickupRequestDetail, PickupStatus, PickupTimelineEvent } from "@/types/pickup";
import type { CollectorSummary } from "@/types/collector";
import type {
  AppNotification,
  NotificationPage,
} from "@/types/notification";
import type {
  CollectorLocation,
  CollectorMapPayload,
  Navigation,
  NearbyPickup,
  PickupMarker,
  RouteStop,
  RouteSummary,
} from "@/types/map";

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
    email_verified: false,
    email_verified_at: null,
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
    refresh_token: `refresh-token-${user.id}`,
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

const TIMELINE_ORDERS: PickupStatus[] = [
  "pending",
  "accepted",
  "on_the_way",
  "collected",
  "completed",
];

export function createPickupTimeline(status: PickupStatus): PickupTimelineEvent[] {
  const events: PickupTimelineEvent[] = [];
  const order = TIMELINE_ORDERS.indexOf(status);

  if (order < 0) {
    return [
      {
        id: 1,
        status: "pending",
        note: "Pickup request created.",
        created_at: "2026-01-10T08:00:00Z",
        actor_name: "Test Citizen",
        actor_role: "citizen",
      },
    ];
  }

  for (let index = 0; index <= order; index += 1) {
    const eventStatus = TIMELINE_ORDERS[index];
    const hour = String(8 + index).padStart(2, "0");
    events.push({
      id: index + 1,
      status: eventStatus,
      note: `Pickup moved to ${eventStatus}.`,
      created_at: `2026-01-10T${hour}:00:00Z`,
      actor_name: index === 0 ? "Test Citizen" : "Test Collector",
      actor_role: index === 0 ? "citizen" : "collector",
    });
  }

  return events;
}

export function createPickupRequestDetail(
  request: PickupRequest,
): PickupRequestDetail {
  return { ...request, timeline: createPickupTimeline(request.status) };
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

export function createCollectorLocation(
  overrides: Partial<CollectorLocation> = {},
): CollectorLocation {
  return {
    latitude: 22.5726,
    longitude: 88.3639,
    accuracy: 12,
    updated_at: "2026-08-01T10:00:00Z",
    ...overrides,
  };
}

export function createPickupMarker(overrides: Partial<PickupMarker> = {}): PickupMarker {
  return {
    id: 3,
    status: "pending",
    waste_type: "Cardboard",
    address: "12 Green Street, Kolkata",
    latitude: 22.5738,
    longitude: 88.3651,
    distance_km: 1.2,
    eta_minutes: 6,
    ...overrides,
  };
}

export function createRouteStop(overrides: Partial<RouteStop> = {}): RouteStop {
  return {
    pickup_id: 3,
    order: 1,
    status: "pending",
    address: "12 Green Street, Kolkata",
    waste_type: "Cardboard",
    latitude: 22.5738,
    longitude: 88.3651,
    distance_from_previous_km: 1.2,
    eta_minutes: 6,
    ...overrides,
  };
}

export function createRouteSummary(overrides: Partial<RouteSummary> = {}): RouteSummary {
  return {
    stops: [
      createRouteStop(),
      createRouteStop({
        pickup_id: 5,
        order: 2,
        status: "accepted",
        address: "5 Paper Lane, Kolkata",
        waste_type: "Paper",
        latitude: 22.5777,
        longitude: 88.3719,
        distance_from_previous_km: 2.1,
        eta_minutes: 9,
      }),
    ],
    total_distance_km: 3.3,
    total_duration_minutes: 15,
    origin_latitude: 22.5726,
    origin_longitude: 88.3639,
    ...overrides,
  };
}

export function createNearbyPickup(overrides: Partial<NearbyPickup> = {}): NearbyPickup {
  return {
    ...createPickupRequest({ id: 3, waste_type: "Cardboard" }),
    distance_km: 0.8,
    ...overrides,
  };
}

export function createCollectorMapPayload(
  overrides: Partial<CollectorMapPayload> = {},
): CollectorMapPayload {
  return {
    collector: createCollectorLocation(),
    pickups: [
      createPickupMarker(),
      createPickupMarker({
        id: 5,
        status: "accepted",
        waste_type: "Paper",
        latitude: 22.5777,
        longitude: 88.3719,
        distance_km: 0.6,
        eta_minutes: 4,
      }),
    ],
    route: createRouteSummary(),
    nearby_pickups: [
      createNearbyPickup(),
      createNearbyPickup({
        id: 4,
        waste_type: "Glass bottles",
        address: "88 Park Avenue, Kolkata",
        distance_km: 2.3,
      }),
    ],
    radius_km: 5,
    ...overrides,
  };
}

export function createNavigation(overrides: Partial<Navigation> = {}): Navigation {
  return {
    pickup: createPickupRequest({ id: 3, waste_type: "Cardboard" }),
    distance_km: 2.1,
    duration_minutes: 11,
    origin_latitude: 22.5726,
    origin_longitude: 88.3639,
    geometry: [
      { latitude: 22.5726, longitude: 88.3639 },
      { latitude: 22.5732, longitude: 88.3644 },
      { latitude: 22.5738, longitude: 88.3651 },
    ],
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

const MARKETPLACE_LOT_DEFAULTS: MarketplaceInventoryLot = {
  id: 201,
  lot_number: "LOT-2026-000201",
  material_category_id: 1,
  material_category_name: "PET Plastic",
  material_description: "Mixed PET bottles",
  weight_kg: 42.5,
  unit_price_per_kg_snapshot: 18.0,
  total_listed_amount: 765.0,
  currency_code: "INR",
  source_city: "Kolkata",
  quality_grade: null,
  status: "available",
  seller_name: "Test Citizen",
  reserved_at: null,
  reservation_expires_at: null,
  is_reserved_by_me: false,
  created_at: "2026-01-12T10:00:00Z",
};

export function createMarketplaceLot(
  overrides: Partial<MarketplaceInventoryLot> = {},
): MarketplaceInventoryLot {
  return { ...MARKETPLACE_LOT_DEFAULTS, ...overrides };
}

export function createMarketplaceLotPage(
  overrides: Partial<MarketplaceInventoryPage> = {},
): MarketplaceInventoryPage {
  return {
    items: [createMarketplaceLot()],
    page: 1,
    page_size: 12,
    total_items: 1,
    total_pages: 1,
    ...overrides,
  };
}

export function createMarketplaceTransaction(
  overrides: Partial<MarketplaceTransaction> = {},
): MarketplaceTransaction {
  return {
    id: 501,
    order_id: null,
    inventory_lot_id: 201,
    lot_number: "LOT-2026-000201",
    material_category_name: "PET Plastic",
    dealer_id: 3,
    dealer_name: "Test Dealer",
    transaction_type: "reservation" as MarketplaceTransactionType,
    status: "completed",
    quantity_kg: 42.5,
    unit_price_per_kg_snapshot: 18.0,
    total_amount: 765.0,
    currency_code: "INR",
    created_at: "2026-01-12T10:05:00Z",
    ...overrides,
  };
}

export function createMarketplaceTransactionPage(
  overrides: Partial<MarketplaceTransactionPage> = {},
): MarketplaceTransactionPage {
  return {
    items: [createMarketplaceTransaction()],
    page: 1,
    page_size: 20,
    total_items: 1,
    total_pages: 1,
    ...overrides,
  };
}

export function createMarketplaceOrder(
  overrides: Partial<MarketplaceOrder> = {},
): MarketplaceOrder {
  return {
    id: 301,
    order_number: "ORD-2026-000301",
    inventory_lot_id: 201,
    lot_number: "LOT-2026-000201",
    material_category_id: 1,
    material_category_name: "PET Plastic",
    material_description: "Mixed PET bottles",
    dealer_id: 3,
    dealer_name: "Test Dealer",
    quantity_kg: 42.5,
    unit_price_per_kg_snapshot: 18.0,
    total_amount: 765.0,
    currency_code: "INR",
    status: "completed",
    created_at: "2026-01-12T10:05:00Z",
    updated_at: "2026-01-12T10:05:00Z",
    ...overrides,
  };
}

export function createMarketplaceOrderDetail(
  overrides: Partial<MarketplaceOrderDetail> = {},
): MarketplaceOrderDetail {
  return {
    ...createMarketplaceOrder(),
    transactions: [
      createMarketplaceTransaction({ transaction_type: "reservation" }),
      createMarketplaceTransaction({
        id: 502,
        order_id: 301,
        transaction_type: "purchase",
      }),
    ],
    ...overrides,
  };
}

export function createMarketplaceOrderPage(
  overrides: Partial<MarketplaceOrderPage> = {},
): MarketplaceOrderPage {
  return {
    items: [createMarketplaceOrder()],
    page: 1,
    page_size: 20,
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
    postal_code: "700001",
    materials_accepted: ["plastic", "paper"],
    approval_status: "submitted",
    rejected_reason: null,
    approved_at: null,
    profile_completion: 80,
    created_at: "2026-01-05T00:00:00Z",
    ...overrides,
  };
}

export function createAdminDealerListPage(
  overrides: Partial<AdminDealerListPage> = {},
): AdminDealerListPage {
  return {
    items: [createAdminDealer()],
    page: 1,
    page_size: 20,
    total_items: 1,
    total_pages: 1,
    ...overrides,
  };
}

export function createDealerProfile(
  overrides: Partial<DealerProfile> = {},
): DealerProfile {
  return {
    id: 11,
    user_id: 3,
    business_name: "Green Scrap Co",
    owner_name: "Test Dealer",
    phone: "+15550000003",
    email: "dealer@example.com",
    address: "12 Green Street, Kolkata",
    city: "Kolkata",
    state: "West Bengal",
    postal_code: "700001",
    gst_number: "19ABCDE1234F1Z5",
    license_number: null,
    business_type: "Scrap dealer",
    profile_image: null,
    description: "Local scrap buying and recycling business.",
    materials_accepted: ["plastic", "paper"],
    approval_status: "approved",
    rejection_reason: null,
    is_verified: true,
    approved_at: "2026-01-06T09:00:00Z",
    created_at: "2026-01-05T08:00:00Z",
    updated_at: "2026-01-06T09:00:00Z",
    profile_completion: 100,
    ...overrides,
  };
}

export function createDealerApprovalEvent(
  overrides: Partial<DealerApprovalEvent> = {},
): DealerApprovalEvent {
  return {
    id: 1,
    status: "submitted",
    note: "Profile submitted for review.",
    actor_name: "Test Dealer",
    actor_role: "dealer",
    created_at: "2026-01-05T09:00:00Z",
    ...overrides,
  };
}

export function createDealerApprovalAction(
  overrides: Partial<DealerApprovalAction> = {},
): DealerApprovalAction {
  return {
    profile_id: 11,
    user_id: 3,
    approval_status: "approved" as DealerApprovalStatus,
    rejection_reason: null,
    is_verified: true,
    approved_at: "2026-01-06T09:00:00Z",
    updated_at: "2026-01-06T09:00:00Z",
    ...overrides,
  };
}

export function createAnalyticsOverview(
  overrides: Partial<AnalyticsOverview> = {},
): AnalyticsOverview {
  return {
    total_users: 1248,
    citizens: 1020,
    collectors: 168,
    dealers: 42,
    total_pickups: 3560,
    completed_pickups: 3104,
    pending_pickups: 220,
    cancelled_pickups: 236,
    total_weight_kg: 18920.5,
    completed_rate: 87.19,
    ...overrides,
  };
}

export function createMaterialBreakdown(
  overrides: Partial<MaterialBreakdown> = {},
): MaterialBreakdown {
  return {
    plastic: 640,
    paper: 410,
    metal: 280,
    glass: 190,
    e_waste: 130,
    organic: 60,
    other: 25,
    ...overrides,
  };
}

const MONTHLY_FIXTURE: Array<Omit<MonthlyStat, "month">> = [
  { pickup_count: 210, completed: 180, weight: 840.5 },
  { pickup_count: 235, completed: 201, weight: 940.2 },
  { pickup_count: 248, completed: 212, weight: 990.8 },
  { pickup_count: 260, completed: 228, weight: 1050.1 },
  { pickup_count: 275, completed: 240, weight: 1110.4 },
  { pickup_count: 290, completed: 254, weight: 1170.7 },
  { pickup_count: 305, completed: 268, weight: 1230.9 },
  { pickup_count: 318, completed: 281, weight: 1290.3 },
  { pickup_count: 330, completed: 292, weight: 1350.6 },
  { pickup_count: 345, completed: 306, weight: 1410.2 },
  { pickup_count: 360, completed: 320, weight: 1470.5 },
  { pickup_count: 384, completed: 342, weight: 1550.0 },
];

export function createMonthlyAnalytics(
  overrides: Partial<MonthlyStat>[] = [],
): MonthlyStat[] {
  return MONTHLY_FIXTURE.map((stats, index) => {
    const monthIndex = 8 + index;
    const year = 2025 + Math.floor(monthIndex / 12);
    const month = `${year}-${String((monthIndex % 12) + 1).padStart(2, "0")}`;
    return { month, ...stats, ...overrides[index] };
  });
}

export function createCollectorPerformance(
  overrides: Partial<CollectorPerformance>[] = [],
): CollectorPerformance[] {
  const collectors = [
    {
      collector_id: 2,
      collector_name: "Test Collector",
      completed_jobs: 156,
      completion_rate: 92.3,
      average_response_time: 1.8,
    },
    {
      collector_id: 7,
      collector_name: "Priya Sharma",
      completed_jobs: 121,
      completion_rate: 88.1,
      average_response_time: 2.4,
    },
  ];
  return collectors.map((collector, index) => ({
    ...collector,
    ...overrides[index],
  }));
}

export function createDealerPerformance(
  overrides: Partial<DealerPerformance>[] = [],
): DealerPerformance[] {
  const dealers = [
    {
      dealer_id: 3,
      dealer_name: "Green Scrap Co",
      materials_processed: 48,
      total_weight: 2140.5,
    },
  ];
  return dealers.map((dealer, index) => ({ ...dealer, ...overrides[index] }));
}

export function createCarbonSavings(
  overrides: Partial<CarbonSavings> = {},
): CarbonSavings {
  return {
    estimated_co2_saved: 7946.6,
    trees_equivalent: 378.4,
    plastic_recycled: 11240.2,
    paper_recycled: 7680.3,
    ...overrides,
  };
}

export function createAnalyticsInsights(
  overrides: Partial<AnalyticsInsight>[] = [],
): AnalyticsInsight[] {
  const insights = [
    {
      key: "most_recycled_material",
      title: "Most Recycled Material",
      message: "Plastic is the most recycled material with 640 completed pickups.",
    },
    {
      key: "top_collector",
      title: "Highest Performing Collector",
      message:
        "Test Collector leads collectors with 156 completed jobs and a 92.3% completion rate.",
    },
    {
      key: "top_dealer",
      title: "Highest Performing Dealer",
      message:
        "Green Scrap Co processed the most material with 2140.5 kg across 48 lots.",
    },
    {
      key: "carbon_savings",
      title: "Estimated Carbon Savings",
      message:
        "The platform has saved an estimated 7946.6 kg of CO2, equivalent to 378.4 trees.",
    },
    {
      key: "pickup_trend",
      title: "Pickup Completion Trend",
      message:
        "Completed pickups are up 12.5% in the last 6 months compared to the previous 6 months.",
    },
  ];
  return insights.map((insight, index) => ({ ...insight, ...overrides[index] }));
}

export function createNotification(
  overrides: Partial<AppNotification> = {},
): AppNotification {
  return {
    id: 701,
    user_id: 1,
    title: "Pickup request created",
    message: "Your pickup request has been created successfully.",
    type: "pickup_created",
    status: "unread",
    link: "/dashboard/pickups/1",
    metadata_json: { pickup_request_id: 1 },
    read_at: null,
    created_at: "2026-01-05T09:00:00Z",
    ...overrides,
  };
}

export function createNotificationPage(
  items: AppNotification[],
  overrides: Partial<NotificationPage> = {},
): NotificationPage {
  const pageSize = overrides.page_size ?? 20;
  return {
    items,
    page: 1,
    page_size: pageSize,
    total_items: items.length,
    total_pages: Math.max(1, Math.ceil(items.length / pageSize)),
    ...overrides,
  };
}
