import api from "./client";

export async function getCitizenDashboardSummary() {
  const response = await api.get("/pickup-requests/citizen/summary");
  return response.data;
}

export async function listPickupRequests() {
  const response = await api.get("/pickup-requests");
  return response.data;
}

export async function getPickupRequestDetail(requestId) {
  const response = await api.get(`/pickup-requests/${requestId}`);
  return response.data;
}

export async function createPickupRequest(payload) {
  const response = await api.post("/pickup-requests", payload);
  return response.data;
}

export async function cancelPickupRequest(requestId) {
  const response = await api.post(`/pickup-requests/${requestId}/cancel`);
  return response.data;
}

export async function acceptPickupRequest(requestId) {
  const response = await api.post(`/collector/accept/${requestId}`);
  return response.data;
}

export async function startPickupRequest(requestId) {
  const response = await api.post(`/collector/start/${requestId}`);
  return response.data;
}

export async function collectPickupRequest(requestId) {
  const response = await api.post(`/collector/collect/${requestId}`);
  return response.data;
}

export async function completePickupRequest(requestId, payload) {
  const response = await api.post(`/collector/complete/${requestId}`, payload);
  return response.data;
}
