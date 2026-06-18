export const requestStatusConfig = {
  pending: {
    label: "Pending",
    badgeClassName: "bg-amber-100 text-amber-800"
  },
  accepted: {
    label: "Accepted",
    badgeClassName: "bg-sky-100 text-sky-800"
  },
  on_the_way: {
    label: "On The Way",
    badgeClassName: "bg-indigo-100 text-indigo-800"
  },
  collected: {
    label: "Collected",
    badgeClassName: "bg-teal-100 text-teal-800"
  },
  completed: {
    label: "Completed",
    badgeClassName: "bg-emerald-100 text-emerald-800"
  },
  cancelled: {
    label: "Cancelled",
    badgeClassName: "bg-rose-100 text-rose-800"
  },
  citizen: {
    label: "Citizen",
    badgeClassName: "bg-orange-100 text-orange-800"
  },
  collector: {
    label: "Collector",
    badgeClassName: "bg-lime-100 text-lime-800"
  },
  admin: {
    label: "Admin",
    badgeClassName: "bg-stone-200 text-stone-800"
  }
};

export const citizenTimelineFlow = ["pending", "accepted", "on_the_way", "collected", "completed"];

export function formatRequestStatus(status) {
  return requestStatusConfig[status]?.label || String(status || "").replaceAll("_", " ");
}

export function getStatusBadgeClassName(status) {
  return requestStatusConfig[status]?.badgeClassName || "bg-stone-200 text-stone-800";
}

export function formatDateTime(value) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
