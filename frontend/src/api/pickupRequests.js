import api from "./client";

function dataOnly(request) {
  return request.then((response) => response.data);
}

export function createPickupRequest(payload) {
  const config = payload instanceof FormData ? { headers: { "Content-Type": "multipart/form-data" } } : {};
  return dataOnly(api.post("/pickup-requests", payload, config));
}

export function listPickupRequests() {
  return dataOnly(api.get("/pickup-requests"));
}

export function getPickupRequestDetail(requestId) {
  return dataOnly(api.get(`/pickup-requests/${requestId}`));
}

export function updatePickupRequest(requestId, payload) {
  return dataOnly(api.patch(`/pickup-requests/${requestId}`, payload));
}

export function cancelPickupRequest(requestId) {
  return dataOnly(api.post(`/pickup-requests/${requestId}/cancel`));
}

export function getCitizenDashboardSummary() {
  return dataOnly(api.get("/pickup-requests/citizen/summary"));
}
