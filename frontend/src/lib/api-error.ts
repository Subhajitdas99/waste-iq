import { isAxiosError, AxiosError } from "axios";

export interface StructuredErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown> | null;
    request_id: string;
  };
}

export interface LegacyErrorResponse {
  detail?: string | { msg?: string }[] | Record<string, unknown>;
  message?: string;
}

export type ApiErrorResponse = StructuredErrorResponse | LegacyErrorResponse;

export type ErrorCode =
  | "VALIDATION_ERROR"
  | "INVALID_CREDENTIALS"
  | "AUTHENTICATION_REQUIRED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "CONFLICT"
  | "RATE_LIMITED"
  | "INTERNAL_SERVER_ERROR"
  | "SERVICE_UNAVAILABLE"
  | "GATEWAY_ERROR"
  | "BAD_REQUEST"
  | "EMAIL_DELIVERY_FAILED"
  | "EMAIL_RATE_LIMITED";

const ERROR_CODE_MESSAGES: Partial<Record<ErrorCode, string>> = {
  VALIDATION_ERROR: "Please check the form for errors.",
  INVALID_CREDENTIALS: "Invalid email or password.",
  AUTHENTICATION_REQUIRED: "Please sign in to continue.",
  FORBIDDEN: "You do not have permission to perform this action.",
  NOT_FOUND: "The requested resource was not found.",
  CONFLICT: "This action conflicts with the current state.",
  RATE_LIMITED: "Too many requests. Please try again later.",
  INTERNAL_SERVER_ERROR: "An unexpected error occurred. Please try again later.",
  SERVICE_UNAVAILABLE: "Service is temporarily unavailable.",
  GATEWAY_ERROR: "Upstream service error.",
  BAD_REQUEST: "Invalid request.",
  EMAIL_DELIVERY_FAILED: "Unable to send email. Please try again.",
  EMAIL_RATE_LIMITED: "Email service temporarily unavailable. Please try again later.",
};

function isStructuredErrorResponse(data: unknown): data is StructuredErrorResponse {
  if (!data || typeof data !== "object") return false;
  const d = data as Record<string, unknown>;
  return (
    "error" in d &&
    typeof d.error === "object" &&
    d.error !== null &&
    "code" in (d.error as Record<string, unknown>) &&
    "message" in (d.error as Record<string, unknown>)
  );
}

function isLegacyErrorResponse(data: unknown): data is LegacyErrorResponse {
  if (!data || typeof data !== "object") return false;
  const d = data as Record<string, unknown>;
  return "detail" in d || "message" in d;
}

export function getErrorCode(error: unknown): ErrorCode | null {
  if (!isAxiosError(error)) return null;
  const data = error.response?.data;
  if (isStructuredErrorResponse(data)) {
    return data.error.code as ErrorCode;
  }
  return null;
}

export function getErrorRequestId(error: unknown): string | null {
  if (!isAxiosError(error)) return null;
  const data = error.response?.data;
  if (isStructuredErrorResponse(data)) {
    return data.error.request_id ?? null;
  }
  return null;
}

export function getErrorDetails(error: unknown): Record<string, unknown> | null {
  if (!isAxiosError(error)) return null;
  const data = error.response?.data;
  if (isStructuredErrorResponse(data)) {
    return data.error.details ?? null;
  }
  return null;
}

export function getStructuredErrorMessage(error: unknown): string | null {
  if (!isAxiosError(error)) return null;
  const data = error.response?.data;
  if (isStructuredErrorResponse(data)) {
    return data.error.message ?? null;
  }
  return null;
}

export function getApiErrorMessage(
  error: unknown,
  fallback = "An unexpected error occurred. Please try again."
): string {
  if (!isAxiosError(error)) return fallback;

  const data = error.response?.data;

  if (isStructuredErrorResponse(data)) {
    return data.error.message ?? fallback;
  }

  if (isLegacyErrorResponse(data)) {
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item: { msg?: string }) => item.msg ?? String(item))
        .join(", ");
    }
    if (typeof data.message === "string") return data.message;
  }

  return fallback;
}

export function isNotFoundError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 404) return true;
  const code = getErrorCode(error);
  return code === "NOT_FOUND";
}

export function isForbiddenError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 403) return true;
  const code = getErrorCode(error);
  return code === "FORBIDDEN";
}

export function isAuthenticationError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 401) return true;
  const code = getErrorCode(error);
  return code === "AUTHENTICATION_REQUIRED" || code === "INVALID_CREDENTIALS";
}

export function isValidationError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 422) return true;
  const code = getErrorCode(error);
  return code === "VALIDATION_ERROR";
}

export function isConflictError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 409) return true;
  const code = getErrorCode(error);
  return code === "CONFLICT";
}

export function isRateLimitError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 429) return true;
  const code = getErrorCode(error);
  return code === "RATE_LIMITED";
}

export function isServerError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 500 || status === 502 || status === 503) return true;
  const code = getErrorCode(error);
  return (
    code === "INTERNAL_SERVER_ERROR" ||
    code === "SERVICE_UNAVAILABLE" ||
    code === "GATEWAY_ERROR"
  );
}

export function isEmailDeliveryError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 503) return true;
  const code = getErrorCode(error);
  return code === "EMAIL_DELIVERY_FAILED" || code === "SERVICE_UNAVAILABLE";
}

export function isEmailRateLimitError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status === 429) return true;
  const code = getErrorCode(error);
  return code === "EMAIL_RATE_LIMITED" || code === "RATE_LIMITED";
}

export function isNetworkError(error: unknown): boolean {
  if (!isAxiosError(error)) return false;
  if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND" || error.code === "ETIMEDOUT") {
    return true;
  }
  if (!error.response) return true;
  return false;
}

export function getRateLimitRetryAfterSeconds(error: unknown): number | null {
  if (!isAxiosError(error)) return null;
  const header = error.response?.headers?.["retry-after"];
  const seconds = Number(header);
  return Number.isFinite(seconds) && seconds > 0 ? Math.ceil(seconds) : null;
}

export function getValidationErrors(error: unknown): Record<string, string[]> | null {
  if (!isAxiosError(error)) return null;

  const data = error.response?.data;

  if (isStructuredErrorResponse(data) && data.error.details) {
    const details = data.error.details;
    if (typeof details === "object" && details !== null) {
      const result: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(details)) {
        if (key === "_general") {
          continue;
        }
        if (typeof value === "string") {
          result[key] = [value];
        } else if (Array.isArray(value)) {
          result[key] = value.map((v) => String(v));
        }
      }
      return Object.keys(result).length > 0 ? result : null;
    }
    return null;
  }

  if (isLegacyErrorResponse(data) && Array.isArray(data.detail)) {
    const errors: Record<string, string[]> = {};
    for (const item of data.detail) {
      if (typeof item === "object" && item !== null) {
        const loc = (item as { loc?: (string | number)[] }).loc;
        const msg = (item as { msg?: string }).msg;
        if (loc && msg) {
          const field = loc[loc.length - 1];
          const fieldKey = typeof field === "number" ? String(field) : field;
          if (!errors[fieldKey]) {
            errors[fieldKey] = [];
          }
          errors[fieldKey].push(msg);
        }
      }
    }
    return Object.keys(errors).length > 0 ? errors : null;
  }

  return null;
}

export function getGeneralValidationErrors(error: unknown): string[] | null {
  if (!isAxiosError(error)) return null;

  const data = error.response?.data;

  if (isStructuredErrorResponse(data) && data.error.details) {
    const details = data.error.details;
    if (typeof details === "object" && details !== null && "_general" in details) {
      const general = details._general;
      if (Array.isArray(general)) {
        return general.map((g) => String(g));
      }
    }
  }

  if (isLegacyErrorResponse(data)) {
    if (typeof data.detail === "string") return [data.detail];
    if (Array.isArray(data.detail)) {
      const messages: string[] = [];
      for (const item of data.detail) {
        if (typeof item === "object" && item !== null) {
          const msg = (item as { msg?: string }).msg;
          if (msg) messages.push(msg);
        }
      }
      if (messages.length > 0) return messages;
    }
    if (typeof data.message === "string") return [data.message];
  }

  return null;
}

export function getUserFriendlyMessage(error: unknown): string {
  if (isNetworkError(error)) {
    return "Network error. Please check your connection and try again.";
  }

  const code = getErrorCode(error);
  if (code && ERROR_CODE_MESSAGES[code]) {
    return ERROR_CODE_MESSAGES[code]!;
  }

  const status = isAxiosError(error) ? error.response?.status : null;
  if (status === 401) {
    return "Please sign in to continue.";
  }
  if (status === 403) {
    return "You do not have permission to perform this action.";
  }
  if (status === 404) {
    return "The requested resource was not found.";
  }
  if (status === 429) {
    return "Too many requests. Please try again later.";
  }
  if (status && status >= 500) {
    return "Server error. Please try again later.";
  }

  return getApiErrorMessage(error);
}

export function createApiError(
  message: string,
  status?: number,
  code?: ErrorCode
): AxiosError {
  const responseData = status && code
    ? {
        error: {
          code,
          message,
          details: null,
          request_id: "test-request-id",
        },
      }
    : { detail: message };
  const err = Object.setPrototypeOf(
    {
      message,
      name: "AxiosError",
      code: "API_ERROR",
      isAxiosError: true,
      response: {
        data: responseData,
        status: status ?? 500,
        statusText: "Error",
        headers: {},
        config: {},
      },
      config: {},
    },
    AxiosError.prototype
  );
  return err as AxiosError;
}
