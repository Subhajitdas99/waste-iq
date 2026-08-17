export function formatMarketplaceCurrency(amount: number, currency = "INR"): string {
  if (currency === "INR") {
    return `₹${amount.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
  return `${currency} ${amount.toFixed(2)}`;
}

export function formatMarketplaceDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatReservationCountdown(expiresAt: string | null | undefined): string {
  if (!expiresAt) {
    return "—";
  }
  const expires = new Date(expiresAt).getTime();
  if (Number.isNaN(expires)) {
    return "—";
  }
  const remainingMs = expires - Date.now();
  if (remainingMs <= 0) {
    return "Expired";
  }
  const totalMinutes = Math.floor(remainingMs / 60_000);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours > 0 ? `${hours}h ${minutes}m remaining` : `${minutes}m remaining`;
}

export function formatMarketplaceStatus(status: string): string {
  return status.replace(/_/g, " ");
}
