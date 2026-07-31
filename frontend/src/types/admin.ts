import type { UserRole } from "@/types/auth";
import type { DealerVerificationStatus } from "@/types/dealer";

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
  pincode: string | null;
  materials_accepted: string[];
  verification_status: DealerVerificationStatus;
  approved_at: string | null;
  profile_completion: number;
  created_at: string;
}
