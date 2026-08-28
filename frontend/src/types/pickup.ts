export type PickupStatus =
  | "pending"
  | "accepted"
  | "on_the_way"
  | "collected"
  | "weight_recorded"
  | "disputed"
  | "completed"
  | "cancelled";

export interface CollectorAssignment {
  id: number;
  collector_id: number;
  collector_name: string;
  accepted_at: string;
  completed_at: string | null;
  weight_kg: number | null;
}

export interface PickupDispute {
  id: number;
  request_id: number;
  reason: string;
  disputed_at: string;
  resolved_at: string | null;
  resolution: "upheld" | "corrected" | null;
  resolved_weight_kg: number | null;
  resolution_notes: string | null;
  resolved_by_id: number | null;
}

export interface PickupRequest {
  id: number;
  user_id: number;
  citizen_name: string;
  citizen_phone: string | null;
  waste_type: string;
  category: string | null;
  confidence: number | null;
  image_url: string | null;
  address: string;
  latitude: number;
  longitude: number;
  estimated_weight_kg: number | null;
  preferred_time: string | null;
  notes: string | null;
  status: PickupStatus;
  created_at: string;
  assigned_collector_name: string | null;
  can_cancel: boolean;
  assignment: CollectorAssignment | null;
}

export interface PickupTimelineEvent {
  id: number;
  status: PickupStatus;
  note: string | null;
  created_at: string;
  actor_name: string | null;
  actor_role: string | null;
}

export interface PickupRequestDetail extends PickupRequest {
  timeline: PickupTimelineEvent[];
  dispute?: PickupDispute | null;
}

export interface CitizenRequestSummary {
  total_requests: number;
  pending_requests: number;
  accepted_requests: number;
  completed_requests: number;
}

export interface PickupRequestUpdatePayload {
  waste_type?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
}

export interface CreatePickupRequestPayload {
  waste_type: string;
  address: string;
  latitude: number;
  longitude: number;
  estimated_weight_kg?: number | null;
  preferred_time?: string | null;
  notes?: string | null;
  image?: File | null;
}

export interface PickupFilters {
  query: string;
  status: "all" | PickupStatus;
  sort: "newest" | "oldest" | "status";
}

export interface ContactSessionRead {
  session_id: string;
  pickup_id: number;
  status: string;
  masked_number: string | null;
  instructions: string;
  expires_at: string | null;
}

export interface WeightDisputeRequest {
  reason: string;
}

export interface WeightDisputeResolveRequest {
  resolution: "upheld" | "corrected";
  resolved_weight_kg?: number | null;
  notes?: string | null;
}

export interface DisputedPickupsPage {
  items: PickupRequest[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}
