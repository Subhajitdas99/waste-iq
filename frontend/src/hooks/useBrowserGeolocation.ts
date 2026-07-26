import { useState } from "react";

export interface BrowserPosition {
  latitude: number;
  longitude: number;
}

export function useBrowserGeolocation() {
  const [position, setPosition] = useState<BrowserPosition | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLocating, setIsLocating] = useState(false);

  const requestLocation = () => {
    if (!("geolocation" in navigator)) {
      setError("Geolocation is not supported in this browser.");
      return;
    }

    setIsLocating(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (nextPosition) => {
        setPosition({
          latitude: nextPosition.coords.latitude,
          longitude: nextPosition.coords.longitude,
        });
        setIsLocating(false);
      },
      (nextError) => {
        setError(nextError.message || "Unable to fetch your current location.");
        setIsLocating(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    );
  };

  return {
    position,
    error,
    isLocating,
    requestLocation,
  };
}
