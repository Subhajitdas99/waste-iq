import api from "./client";

function dataOnly(request) {
  return request.then((response) => response.data);
}

export function getCollectorSummary() {
  return dataOnly(api.get("/collector/summary"));
}

export function getNearbyPickups({ latitude, longitude, radiusKm = 5 }) {
  return dataOnly(
    api.get("/collector/nearby", {
      params: {
        latitude,
        longitude,
        radius_km: radiusKm
      }
    })
  );
}

export function getAssignedPickups() {
  return dataOnly(api.get("/collector/assigned"));
}

export function acceptPickup(id) {
  return dataOnly(api.post(`/collector/accept/${id}`));
}

export function startPickup(id) {
  return dataOnly(api.post(`/collector/start/${id}`));
}

export function collectPickup(id) {
  return dataOnly(api.post(`/collector/collect/${id}`));
}

export function completePickup(id, weight) {
  return dataOnly(api.post(`/collector/complete/${id}`, { weight_kg: weight }));
}
