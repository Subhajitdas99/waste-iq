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
