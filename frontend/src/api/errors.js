export function getApiError(error, fallback = "Something went wrong. Please try again.") {
  return error?.response?.data?.detail || fallback;
}
