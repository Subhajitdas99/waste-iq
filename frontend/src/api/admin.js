import api from "./client";

function dataOnly(request) {
  return request.then((response) => response.data);
}

export function getAdminAnalytics() {
  return dataOnly(api.get("/admin/analytics"));
}

export function listAdminUsers() {
  return dataOnly(api.get("/admin/users"));
}
