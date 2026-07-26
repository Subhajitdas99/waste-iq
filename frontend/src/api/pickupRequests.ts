import type { AxiosProgressEvent } from "axios";
import api from "@/api/axios";
import type {
  CitizenRequestSummary,
  CreatePickupRequestPayload,
  PickupRequest,
  PickupRequestDetail,
  PickupRequestUpdatePayload,
} from "@/types/pickup";

function buildPickupFormData(payload: CreatePickupRequestPayload): FormData {
  const formData = new FormData();
  formData.append("waste_type", payload.waste_type.trim());
  formData.append("address", payload.address.trim());
  formData.append("latitude", String(payload.latitude));
  formData.append("longitude", String(payload.longitude));

  if (payload.image) {
    formData.append("image", payload.image);
  }

  return formData;
}

function toProgressValue(event: AxiosProgressEvent): number {
  if (!event.total) {
    return 0;
  }

  return Math.min(100, Math.round((event.loaded * 100) / event.total));
}

export async function listPickupRequests(): Promise<PickupRequest[]> {
  const response = await api.get<PickupRequest[]>("/pickup-requests");
  return response.data;
}

export async function getCitizenRequestSummary(): Promise<CitizenRequestSummary> {
  const response = await api.get<CitizenRequestSummary>("/pickup-requests/citizen/summary");
  return response.data;
}

export async function getPickupRequestDetail(
  requestId: number | string,
): Promise<PickupRequestDetail> {
  const response = await api.get<PickupRequestDetail>(`/pickup-requests/${requestId}`);
  return response.data;
}

export async function createPickupRequest(
  payload: CreatePickupRequestPayload,
  onUploadProgress?: (progress: number) => void,
): Promise<PickupRequest> {
  const response = await api.post<PickupRequest>("/pickup-requests", buildPickupFormData(payload), {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (event) => {
      onUploadProgress?.(toProgressValue(event));
    },
  });

  return response.data;
}

export async function updatePickupRequest(
  requestId: number,
  payload: PickupRequestUpdatePayload,
): Promise<PickupRequest> {
  const response = await api.patch<PickupRequest>(`/pickup-requests/${requestId}`, payload);
  return response.data;
}

export async function cancelPickupRequest(requestId: number): Promise<PickupRequest> {
  const response = await api.post<PickupRequest>(`/pickup-requests/${requestId}/cancel`);
  return response.data;
}
