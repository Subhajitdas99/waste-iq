import { isAxiosError } from "axios";

export function getApiErrorMessage(
  error: unknown,
  fallback = "An unexpected error occurred. Please try again."
): string {
  if (!isAxiosError(error)) return fallback;

  const detail = error.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item: { msg?: string }) => item.msg ?? String(item))
      .join(", ");
  }

  return fallback;
}

export function isNotFoundError(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 404;
}

export function isRateLimitError(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 429;
}

export function getRateLimitRetryAfterSeconds(error: unknown): number | null {
  if (!isAxiosError(error)) return null;
  const header = error.response?.headers?.["retry-after"];
  const seconds = Number(header);
  return Number.isFinite(seconds) && seconds > 0 ? Math.ceil(seconds) : null;
}
