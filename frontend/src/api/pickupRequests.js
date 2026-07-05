import api from "./client";

function dataOnly(request) {
  return request.then((response) => response.data);
}

export function createPickupRequest(payload) {
  return dataOnly(api.post("/pickup-requests", payload));
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

export function getCollectorSummary() {
  return dataOnly(api.get("/collector/summary"));
}

export function acceptPickupRequest(requestId) {
  return dataOnly(api.post(`/collector/accept/${requestId}`));
}

export function startPickupRequest(requestId) {
  return dataOnly(api.post(`/collector/start/${requestId}`));
}

export function collectPickupRequest(requestId) {
  return dataOnly(api.post(`/collector/collect/${requestId}`));
}

export function completePickupRequest({ requestId, weight_kg }) {
  return dataOnly(api.post(`/collector/complete/${requestId}`, { weight_kg }));
}
