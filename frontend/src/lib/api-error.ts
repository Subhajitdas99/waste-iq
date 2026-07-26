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
