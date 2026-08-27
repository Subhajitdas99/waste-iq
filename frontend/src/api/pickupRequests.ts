import type { AxiosProgressEvent } from "axios";
import apiClient from "@/api/client";
import type {
  CitizenRequestSummary,
  ContactSessionRead,
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

  if (typeof payload.estimated_weight_kg === "number") {
    formData.append("estimated_weight_kg", String(payload.estimated_weight_kg));
  }

  if (payload.preferred_time) {
    formData.append("preferred_time", payload.preferred_time);
  }

  if (payload.notes?.trim()) {
    formData.append("notes", payload.notes.trim());
  }

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
  const response = await apiClient.get<PickupRequest[]>("/pickup-requests");
  return response.data;
}

export async function getCitizenRequestSummary(): Promise<CitizenRequestSummary> {
  const response = await apiClient.get<CitizenRequestSummary>("/pickup-requests/citizen/summary");
  return response.data;
}

export async function getPickupRequestDetail(
  requestId: number | string,
): Promise<PickupRequestDetail> {
  const response = await apiClient.get<PickupRequestDetail>(`/pickup-requests/${requestId}`);
  return response.data;
}

export async function createPickupRequest(
  payload: CreatePickupRequestPayload,
  onUploadProgress?: (progress: number) => void,
): Promise<PickupRequest> {
  const response = await apiClient.post<PickupRequest>("/pickup-requests", buildPickupFormData(payload), {
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
  const response = await apiClient.patch<PickupRequest>(`/pickup-requests/${requestId}`, payload);
  return response.data;
}

export async function cancelPickupRequest(requestId: number): Promise<PickupRequest> {
  const response = await apiClient.post<PickupRequest>(`/pickup-requests/${requestId}/cancel`);
  return response.data;
}

export async function initiateContact(requestId: number): Promise<ContactSessionRead> {
  const response = await apiClient.post<ContactSessionRead>(`/pickup-requests/${requestId}/contact`);
  return response.data;
}
