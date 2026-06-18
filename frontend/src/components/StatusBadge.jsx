import { formatRequestStatus, getStatusBadgeClassName } from "../utils/pickupRequests";

export default function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${getStatusBadgeClassName(status)}`}
    >
      {formatRequestStatus(status)}
    </span>
  );
}
