import { useQuery } from "@tanstack/react-query";

import { getNearbyPickups } from "../api/collector";
import { collectorQueryKeys } from "./useCollectorDashboard";

export function useNearbyPickups(location, radiusKm = 5) {
  const latitude = location?.latitude;
  const longitude = location?.longitude;

  return useQuery({
    queryKey: collectorQueryKeys.nearbyPickups(latitude, longitude, radiusKm),
    queryFn: () => getNearbyPickups({ latitude, longitude, radiusKm }),
    enabled: Number.isFinite(latitude) && Number.isFinite(longitude)
  });
}
