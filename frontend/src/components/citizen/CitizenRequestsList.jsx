import { Eye, Table2, XCircle } from "lucide-react";
import { Link } from "react-router-dom";

import StatusBadge from "../StatusBadge";
import { formatDateTime } from "../../utils/pickupRequests";

function CitizenRequestActions({ request, busyRequestId, onCancel }) {
  return (
    <div className="flex flex-wrap gap-3">
      <Link
        to={`/dashboard/requests/${request.id}`}
        className="inline-flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/80 px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink/20"
      >
        <Eye className="h-4 w-4" />
        View details
      </Link>
      {request.can_cancel ? (
        <button
          type="button"
          onClick={() => onCancel(request.id)}
          disabled={busyRequestId === request.id}
          className="inline-flex items-center gap-2 rounded-2xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-600 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <XCircle className="h-4 w-4" />
          {busyRequestId === request.id ? "Cancelling..." : "Cancel"}
        </button>
      ) : null}
    </div>
  );
}

function CitizenRequestCards({ requests, busyRequestId, onCancel }) {
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      {requests.map((request) => (
        <article key={request.id} className="glass-panel rounded-[2rem] border border-white/60 p-5 shadow-glow">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Request #{request.id}</p>
              <h3 className="mt-2 font-display text-2xl text-ink">{request.waste_type}</h3>
            </div>
            <StatusBadge status={request.status} />
          </div>

          <dl className="mt-5 space-y-3 text-sm text-ink/75">
            <div>
              <dt className="text-xs uppercase tracking-[0.28em] text-ink/45">Address</dt>
              <dd className="mt-1">{request.address}</dd>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <dt className="text-xs uppercase tracking-[0.28em] text-ink/45">Created date</dt>
                <dd className="mt-1">{formatDateTime(request.created_at)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-[0.28em] text-ink/45">Assigned collector</dt>
                <dd className="mt-1">{request.assigned_collector_name || "Not assigned yet"}</dd>
              </div>
            </div>
          </dl>

          <div className="mt-5">
            <CitizenRequestActions request={request} busyRequestId={busyRequestId} onCancel={onCancel} />
          </div>
        </article>
      ))}
    </div>
  );
}

export default function CitizenRequestsList({ requests, viewMode, busyRequestId, onCancel }) {
  if (viewMode === "cards") {
    return <CitizenRequestCards requests={requests} busyRequestId={busyRequestId} onCancel={onCancel} />;
  }

  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/60 bg-white/55 shadow-glow">
      <div className="flex items-center gap-2 border-b border-white/60 bg-white/35 px-5 py-4 text-sm text-ink/60">
        <Table2 className="h-4 w-4" />
        Request table
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm text-ink/75">
          <thead className="bg-white/30 text-xs uppercase tracking-[0.28em] text-ink/55">
            <tr>
              <th className="px-5 py-4">Waste Type</th>
              <th className="px-5 py-4">Address</th>
              <th className="px-5 py-4">Status</th>
              <th className="px-5 py-4">Created Date</th>
              <th className="px-5 py-4">Assigned Collector</th>
              <th className="px-5 py-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((request) => (
              <tr key={request.id} className="border-t border-white/60 bg-white/20 align-top">
                <td className="px-5 py-4 font-semibold text-ink">{request.waste_type}</td>
                <td className="px-5 py-4">{request.address}</td>
                <td className="px-5 py-4">
                  <StatusBadge status={request.status} />
                </td>
                <td className="px-5 py-4">{formatDateTime(request.created_at)}</td>
                <td className="px-5 py-4">{request.assigned_collector_name || "Not assigned yet"}</td>
                <td className="px-5 py-4">
                  <CitizenRequestActions request={request} busyRequestId={busyRequestId} onCancel={onCancel} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
