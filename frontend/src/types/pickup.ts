export type PickupStatus =
  | "pending"
  | "accepted"
  | "on_the_way"
  | "collected"
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
  image?: File | null;
}

export interface PickupFilters {
  query: string;
  status: "all" | PickupStatus;
  sort: "newest" | "oldest" | "status";
}
