export type UserRole = "citizen" | "collector" | "dealer" | "admin";

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: UserRole;
  created_at: string;
  email_verified: boolean;
  email_verified_at: string | null;
}

export interface ActionMessageResponse {
  message: string;
}

export interface VerifyEmailPayload {
  token: string;
}

export interface ResendVerificationPayload {
  email: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  user: UserProfile;
}

export type LoginHistoryOutcome = "success" | "failure";

export interface LoginHistoryEntry {
  id: number;
  outcome: LoginHistoryOutcome;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface LoginHistoryResponse {
  items: LoginHistoryEntry[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface LoginHistoryParams {
  page?: number;
  page_size?: number;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  phone: string;
  password: string;
  role: UserRole;
  adminCode?: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  newPassword: string;
}
