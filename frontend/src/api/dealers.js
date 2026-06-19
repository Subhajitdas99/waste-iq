import api from "./client";

export async function getDealerProfile() {
  const response = await api.get("/dealer/profile");
  return response.data;
}

export async function createDealerProfile(payload) {
  const response = await api.post("/dealer/profile", payload);
  return response.data;
}

export async function updateDealerProfile(payload) {
  const response = await api.patch("/dealer/profile", payload);
  return response.data;
}

export async function listAdminDealers() {
  const response = await api.get("/admin/dealers");
  return response.data;
}

export async function approveDealer(dealerUserId) {
  const response = await api.post(`/admin/dealers/${dealerUserId}/approve`);
  return response.data;
}

export async function rejectDealer(dealerUserId) {
  const response = await api.post(`/admin/dealers/${dealerUserId}/reject`);
  return response.data;
}
