import { useCallback, useEffect, useRef, useState } from "react";

import { useToast } from "../components/ui/toast";

const GEOLOCATION_OPTIONS = {
  enableHighAccuracy: true,
  maximumAge: 30000,
  timeout: 10000
};

function getGeolocationErrorMessage(error) {
  if (error?.code === 1) {
    return "Location permission was denied. Allow location access in your browser and retry.";
  }

  if (error?.code === 2) {
    return "Your current location is unavailable. Check device location settings and retry.";
  }

  if (error?.code === 3) {
    return "Location request timed out. Move to a stronger signal area and retry.";
  }

  return "Unable to read your current location. Please retry.";
}

export function useBrowserGeolocation({
  enabled = true,
  autoStart = true,
  watch = false,
  errorTitle = "Location unavailable"
} = {}) {
  const { toast } = useToast();
  const watchIdRef = useRef(null);
  const [position, setPosition] = useState(null);
  const [error, setError] = useState("");
  const [isLocating, setIsLocating] = useState(false);

  const clearLocationWatch = useCallback(() => {
    if (watchIdRef.current !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
  }, []);

  const showError = useCallback(
    (message) => {
      setError(message);
      toast({
        title: errorTitle,
        description: message,
        variant: "error"
      });
    },
    [errorTitle, toast]
  );

  const requestLocation = useCallback(() => {
    if (!enabled) {
      return;
    }

    setError("");

    if (!navigator.geolocation) {
      showError("Geolocation is not supported by this browser.");
      return;
    }

    setIsLocating(true);

    const handleSuccess = (nextPosition) => {
      setPosition({
        latitude: nextPosition.coords.latitude,
        longitude: nextPosition.coords.longitude,
        accuracy: nextPosition.coords.accuracy
      });
      setError("");
      setIsLocating(false);
    };

    const handleError = (nextError) => {
      clearLocationWatch();
      setIsLocating(false);
      showError(getGeolocationErrorMessage(nextError));
    };

    if (watch) {
      clearLocationWatch();
      watchIdRef.current = navigator.geolocation.watchPosition(
        handleSuccess,
        handleError,
        GEOLOCATION_OPTIONS
      );
      return;
    }

    navigator.geolocation.getCurrentPosition(handleSuccess, handleError, GEOLOCATION_OPTIONS);
  }, [clearLocationWatch, enabled, showError, watch]);

  useEffect(() => {
    if (enabled && autoStart) {
      requestLocation();
    }

    return clearLocationWatch;
  }, [autoStart, clearLocationWatch, enabled, requestLocation]);

  return {
    error,
    isLocating,
    position,
    requestLocation
  };
}
