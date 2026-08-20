import type { AxiosResponse } from "axios";
import apiClient, { type ApiRequestConfig } from "@/api/client";
import type {
  ActionMessageResponse,
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  UserProfile,
} from "@/types/auth";

const publicRequestConfig: ApiRequestConfig = {
  skipAuth: true,
};

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse, AxiosResponse<AuthResponse>>(
    "/auth/login",
    payload,
    publicRequestConfig
  );

  return response.data;
}

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse, AxiosResponse<AuthResponse>>(
    "/auth/register",
    {
      name: payload.name,
      email: payload.email,
      phone: payload.phone,
      password: payload.password,
      role: payload.role,
      ...(payload.role === "admin" && payload.adminCode
        ? { admin_code: payload.adminCode }
        : {}),
    },
    publicRequestConfig
  );

  return response.data;
}

export async function getProfile(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>("/auth/me");
  return response.data;
}

export async function refresh(refreshToken: string): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse, AxiosResponse<AuthResponse>>(
    "/auth/refresh",
    { refresh_token: refreshToken },
    publicRequestConfig
  );
  return response.data;
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post("/auth/logout", { refresh_token: refreshToken });
}

export async function logoutAll(): Promise<void> {
  await apiClient.post("/auth/logout-all");
}

export async function verifyEmail(token: string): Promise<ActionMessageResponse> {
  const response = await apiClient.post<
    ActionMessageResponse,
    AxiosResponse<ActionMessageResponse>
  >("/auth/verify-email", { token }, publicRequestConfig);
  return response.data;
}

export async function resendVerification(
  email: string
): Promise<ActionMessageResponse> {
  const response = await apiClient.post<
    ActionMessageResponse,
    AxiosResponse<ActionMessageResponse>
  >("/auth/resend-verification", { email }, publicRequestConfig);
  return response.data;
}
