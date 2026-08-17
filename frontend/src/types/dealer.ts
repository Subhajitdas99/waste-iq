export type DealerApprovalStatus = "draft" | "submitted" | "approved" | "rejected";

export interface DealerProfile {
  id: number;
  user_id: number;
  business_name: string;
  owner_name: string;
  phone: string;
  email: string | null;
  address: string;
  city: string;
  state: string | null;
  postal_code: string;
  gst_number: string | null;
  license_number: string | null;
  business_type: string | null;
  profile_image: string | null;
  description: string | null;
  materials_accepted: string[];
  approval_status: DealerApprovalStatus;
  rejection_reason: string | null;
  is_verified: boolean;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
  profile_completion: number;
}

export type DealerProfilePayload = Omit<
  DealerProfile,
  | "id"
  | "user_id"
  | "profile_image"
  | "approval_status"
  | "rejection_reason"
  | "is_verified"
  | "approved_at"
  | "created_at"
  | "updated_at"
  | "profile_completion"
>;

export type DealerProfileUpdatePayload = Partial<DealerProfilePayload>;

export interface DealerApprovalEvent {
  id: number;
  status: DealerApprovalStatus;
  note: string | null;
  actor_name: string | null;
  actor_role: string | null;
  created_at: string;
}

export interface DealerApprovalAction {
  profile_id: number;
  user_id: number;
  approval_status: DealerApprovalStatus;
  rejection_reason: string | null;
  is_verified: boolean;
  approved_at: string | null;
  updated_at: string;
}
