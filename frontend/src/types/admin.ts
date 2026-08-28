import type { UserRole } from "@/types/auth";
import type { DealerApprovalEvent, DealerApprovalStatus, DealerProfile } from "@/types/dealer";

export interface RoleBreakdown {
  citizens: number;
  collectors: number;
  dealers: number;
  admins: number;
}

export interface RequestStatusBreakdown {
  pending: number;
  accepted: number;
  on_the_way: number;
  collected: number;
  completed: number;
  cancelled: number;
}

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: UserRole;
  created_at: string;
}

export interface AdminAnalytics {
  total_users: number;
  total_pickup_requests: number;
  total_completed_pickups: number;
  total_collected_weight_kg: number;
  users_by_role: RoleBreakdown;
  requests_by_status: RequestStatusBreakdown;
}

export interface AdminDealerSummary {
  user_id: number;
  user_name: string;
  user_email: string;
  account_phone: string;
  has_profile: boolean;
  business_name: string | null;
  owner_name: string | null;
  city: string | null;
  postal_code: string | null;
  materials_accepted: string[];
  approval_status: DealerApprovalStatus;
  rejected_reason: string | null;
  approved_at: string | null;
  profile_completion: number;
  created_at: string;
}

export interface AdminDealerListPage {
  items: AdminDealerSummary[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface AdminDealerDetail {
  user_id: number;
  user_name: string;
  user_email: string;
  account_phone: string;
  profile: DealerProfile;
  timeline: DealerApprovalEvent[];
}

export interface AdminDealerListQuery {
  page?: number;
  page_size?: number;
  status?: DealerApprovalStatus;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface PilotWindow {
  start: string | null;
  end: string | null;
  days: number;
}

export interface PilotCollectionKpis {
  total_pickups: number;
  completed_pickups: number;
  cancelled_pickups: number;
  completion_rate: number;
  total_weight_kg: number;
  average_weight_kg: number;
  active_citizens: number;
  active_collectors: number;
}

export interface PilotTiming {
  median_request_to_acceptance_hours: number | null;
  median_acceptance_to_completion_hours: number | null;
  median_request_to_completion_hours: number | null;
  average_request_to_acceptance_hours: number | null;
  average_acceptance_to_completion_hours: number | null;
  sample_size: number;
}

export interface PilotWeightQuality {
  pickups_with_estimate: number;
  pickups_with_recorded_weight: number;
  estimate_vs_actual_ratio: number | null;
  median_absolute_estimate_delta_kg: number | null;
  disputed_pickups: number;
  disputes_upheld: number;
  disputes_corrected: number;
}

export interface PilotActivity {
  pickups_last_7_days: number;
  pickups_last_30_days: number;
  completed_last_7_days: number;
  completed_last_30_days: number;
  lots_listed: number;
  lots_sold: number;
  pending_dealer_applications: number;
}

export interface PilotReliability {
  api_error_rate: number | null;
  api_error_rate_available: boolean;
  api_error_rate_note: string;
  notification_failure_rate: number | null;
  notification_failure_rate_available: boolean;
  notification_failure_rate_note: string;
  background_job_failures: number | null;
  background_job_failures_available: boolean;
  background_job_failures_note: string;
  background_job_last_runs: Record<string, string | null>;
  platform_uptime_seconds: number | null;
  platform_uptime_available: boolean;
  platform_uptime_note: string;
}

export interface PilotMetrics {
  window: PilotWindow;
  collection: PilotCollectionKpis;
  timing: PilotTiming;
  weight_quality: PilotWeightQuality;
  activity: PilotActivity;
  reliability: PilotReliability;
}
