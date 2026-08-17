const MINUTE_MS = 60_000;
const HOUR_MS = 60 * MINUTE_MS;
const DAY_MS = 24 * HOUR_MS;

export function formatNotificationTimestamp(isoTimestamp: string, now = new Date()): string {
  const timestamp = new Date(isoTimestamp);
  if (Number.isNaN(timestamp.getTime())) {
    return "";
  }

  const diffMs = now.getTime() - timestamp.getTime();

  if (diffMs < MINUTE_MS) {
    return "Just now";
  }

  if (diffMs < HOUR_MS) {
    const minutes = Math.floor(diffMs / MINUTE_MS);
    return `${minutes}m ago`;
  }

  if (diffMs < DAY_MS) {
    const hours = Math.floor(diffMs / HOUR_MS);
    return `${hours}h ago`;
  }

  const isYesterday =
    new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime() -
      new Date(timestamp.getFullYear(), timestamp.getMonth(), timestamp.getDate()).getTime() ===
    DAY_MS;

  if (isYesterday) {
    return "Yesterday";
  }

  return timestamp.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: timestamp.getFullYear() === now.getFullYear() ? undefined : "numeric",
  });
}