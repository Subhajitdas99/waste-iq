import apiClient from "@/api/client";
import type {
  DealerApprovalEvent,
  DealerProfile,
  DealerProfilePayload,
  DealerProfileUpdatePayload,
} from "@/types/dealer";

export async function getDealerProfile(): Promise<DealerProfile> {
  const response = await apiClient.get<DealerProfile>("/dealer/profile");
  return response.data;
}

export async function createDealerProfile(
  data: DealerProfilePayload,
): Promise<DealerProfile> {
  const response = await apiClient.post<DealerProfile>("/dealer/profile", data);
  return response.data;
}

export async function updateDealerProfile(
  data: DealerProfileUpdatePayload,
): Promise<DealerProfile> {
  const response = await apiClient.put<DealerProfile>("/dealer/profile", data);
  return response.data;
}

export async function submitDealerProfile(): Promise<DealerProfile> {
  const response = await apiClient.post<DealerProfile>("/dealer/profile/submit");
  return response.data;
}

export async function getDealerProfileTimeline(): Promise<DealerApprovalEvent[]> {
  const response = await apiClient.get<DealerApprovalEvent[]>(
    "/dealer/profile/timeline",
  );
  return response.data;
}
