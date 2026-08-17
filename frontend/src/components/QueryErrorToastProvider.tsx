import { useEffect, useState } from "react";
import { Toast } from "@/components/Toast";
import {
  setGlobalQueryErrorHandler,
  type QueryErrorPayload,
} from "@/queryClient";

const ERROR_TOAST_DURATION_MS = 5000;

export function QueryErrorToastProvider() {
  const [activeError, setActiveError] = useState<QueryErrorPayload | null>(null);

  useEffect(() => {
    setGlobalQueryErrorHandler((payload) => {
      setActiveError(payload);
    });

    return () => {
      setGlobalQueryErrorHandler(null);
    };
  }, []);

  useEffect(() => {
    if (!activeError) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setActiveError(null);
    }, ERROR_TOAST_DURATION_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [activeError]);

  if (!activeError) {
    return null;
  }

  return (
    <Toast
      message={activeError.message}
      type="error"
      onDismiss={() => setActiveError(null)}
    />
  );
}
