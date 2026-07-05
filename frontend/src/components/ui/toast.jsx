import * as React from "react";
import { X } from "lucide-react";
import { Toast as ToastPrimitive } from "radix-ui";

import { cn } from "../../lib/utils";

const ToastContext = React.createContext(null);

function getDescription(detail, fallback) {
  if (Array.isArray(detail)) {
    const message = detail
      .map((item) => item?.msg || item?.message)
      .filter(Boolean)
      .join(" ");
    return message || fallback;
  }

  if (typeof detail === "string") {
    return detail;
  }

  return fallback;
}

export function getErrorToast(error, fallback = "Something went wrong. Please try again.") {
  if (!error?.response) {
    return {
      title: "Network error",
      description: "We could not reach Waste-IQ. Please check your connection and try again.",
      variant: "error"
    };
  }

  const status = error.response.status;
  const detail = error.response.data?.detail;

  if (status === 400 || status === 422) {
    return {
      title: "Validation error",
      description: getDescription(detail, fallback),
      variant: "error"
    };
  }

  return {
    title: "Server error",
    description: getDescription(detail, fallback),
    variant: "error"
  };
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = React.useState([]);

  const dismissToast = React.useCallback((toastId) => {
    setToasts((currentToasts) => currentToasts.filter((toast) => toast.id !== toastId));
  }, []);

  const toast = React.useCallback((nextToast) => {
    const id = globalThis.crypto?.randomUUID?.() || `${Date.now()}`;
    setToasts((currentToasts) => [...currentToasts, { id, variant: "success", ...nextToast }]);
    return id;
  }, []);

  const value = React.useMemo(() => ({ dismissToast, toast }), [dismissToast, toast]);

  return (
    <ToastContext.Provider value={value}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}
        <ToastPrimitive.Viewport className="fixed right-4 top-4 z-[100] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-3 outline-none sm:right-6 sm:top-6" />
        {toasts.map((item) => (
          <ToastPrimitive.Root
            key={item.id}
            duration={5000}
            className={cn(
              "pointer-events-auto grid grid-cols-[1fr_auto] gap-3 rounded-3xl border bg-white/95 p-4 text-ink shadow-glow backdrop-blur",
              item.variant === "error" ? "border-coral/40" : "border-leaf/30"
            )}
            onOpenChange={(open) => {
              if (!open) {
                dismissToast(item.id);
              }
            }}
          >
            <div>
              <ToastPrimitive.Title
                className={cn("text-sm font-semibold", item.variant === "error" ? "text-coral" : "text-leaf")}
              >
                {item.title}
              </ToastPrimitive.Title>
              {item.description ? (
                <ToastPrimitive.Description className="mt-1 text-sm leading-6 text-ink/70">
                  {item.description}
                </ToastPrimitive.Description>
              ) : null}
            </div>
            <ToastPrimitive.Close className="rounded-full p-1 text-ink/45 transition hover:bg-ink/5 hover:text-ink">
              <X className="h-4 w-4" />
              <span className="sr-only">Dismiss notification</span>
            </ToastPrimitive.Close>
          </ToastPrimitive.Root>
        ))}
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
