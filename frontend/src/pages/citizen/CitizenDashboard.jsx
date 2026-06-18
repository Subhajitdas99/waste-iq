import { ArrowRight, Clock3, PackageSearch, Truck } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getApiError } from "../../api/client";
import { getCitizenDashboardSummary, listPickupRequests } from "../../api/pickupRequests";
import CitizenQuickCreateForm from "../../components/citizen/CitizenQuickCreateForm";
import MetricCard from "../../components/MetricCard";
import StatusBadge from "../../components/StatusBadge";
import { formatDateTime } from "../../utils/pickupRequests";

function buildSummaryFromRequests(requests) {
  return {
    total_requests: requests.length,
    pending_requests: requests.filter((request) => request.status === "pending").length,
    accepted_requests: requests.filter((request) => request.status === "accepted").length,
    completed_requests: requests.filter((request) => request.status === "completed").length
  };
}

export default function CitizenDashboard() {
  const [summary, setSummary] = useState(null);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    const [summaryResult, requestsResult] = await Promise.allSettled([
      getCitizenDashboardSummary(),
      listPickupRequests()
    ]);

    const nextRequests = requestsResult.status === "fulfilled" ? requestsResult.value : [];
    const nextSummary =
      summaryResult.status === "fulfilled"
        ? summaryResult.value
        : requestsResult.status === "fulfilled"
          ? buildSummaryFromRequests(nextRequests)
          : null;

    setRequests(nextRequests);
    setSummary(nextSummary);

    if (summaryResult.status === "fulfilled" || requestsResult.status === "fulfilled") {
      setError("");
    } else {
      const summaryError = summaryResult.reason ? getApiError(summaryResult.reason, "") : "";
      const requestsError = requestsResult.reason ? getApiError(requestsResult.reason, "") : "";
      setError(summaryError || requestsError || "Unable to load your citizen dashboard.");
    }

    setLoading(false);
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const recentRequests = requests.slice(0, 3);

  return (
    <div className="space-y-8">
      {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="glass-panel overflow-hidden rounded-[2rem] border border-white/60 shadow-glow">
          <div className="bg-gradient-to-br from-ink via-leaf to-moss px-6 py-7 text-sand sm:px-8">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-sand/70">Welcome Back</p>
            <h2 className="mt-3 max-w-2xl font-display text-4xl leading-tight">
              Your neighborhood pickup activity is now easier to track, manage, and close.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-sand/75">
              Use this space to raise a new request, review live statuses, and check which collector has been assigned.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                to="/dashboard/requests"
                className="inline-flex items-center gap-2 rounded-2xl bg-white px-5 py-3 font-semibold text-ink transition hover:bg-sand"
              >
                View all requests
                <ArrowRight className="h-4 w-4" />
              </Link>
              <button
                type="button"
                onClick={loadDashboard}
                className="rounded-2xl border border-white/20 bg-white/10 px-5 py-3 font-semibold text-sand transition hover:bg-white/15"
              >
                Refresh dashboard
              </button>
            </div>
          </div>

          <div className="grid gap-4 bg-white/25 px-6 py-6 sm:grid-cols-3 sm:px-8">
            <div className="rounded-3xl bg-white/75 p-4">
              <Clock3 className="h-6 w-6 text-ember" />
              <p className="mt-4 text-xs font-semibold uppercase tracking-[0.3em] text-ink/55">Live queue</p>
              <p className="mt-2 text-sm text-ink/70">Pending requests stay editable and can still be cancelled.</p>
            </div>
            <div className="rounded-3xl bg-white/75 p-4">
              <Truck className="h-6 w-6 text-leaf" />
              <p className="mt-4 text-xs font-semibold uppercase tracking-[0.3em] text-ink/55">Collector sync</p>
              <p className="mt-2 text-sm text-ink/70">Assigned collectors appear in your request feed as soon as a job is accepted.</p>
            </div>
            <div className="rounded-3xl bg-white/75 p-4">
              <PackageSearch className="h-6 w-6 text-moss" />
              <p className="mt-4 text-xs font-semibold uppercase tracking-[0.3em] text-ink/55">Timeline view</p>
              <p className="mt-2 text-sm text-ink/70">Open any request to inspect every transition from creation to completion.</p>
            </div>
          </div>
        </div>

        <section className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Create Pickup</p>
          <h2 className="mt-3 font-display text-3xl text-ink">Schedule a new waste pickup</h2>
          <p className="mt-2 text-sm text-ink/70">
            Add the waste type, address, and optional photo so collectors have enough context before accepting.
          </p>
          <div className="mt-6">
            <CitizenQuickCreateForm onCreated={loadDashboard} />
          </div>
        </section>
      </section>

      {loading && !summary ? <p className="text-sm text-ink/70">Loading dashboard metrics...</p> : null}

      {summary ? (
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Total Requests" value={summary.total_requests} hint="All pickup requests you have created" />
          <MetricCard label="Pending Requests" value={summary.pending_requests} hint="Still waiting for a collector to accept" />
          <MetricCard label="Accepted Requests" value={summary.accepted_requests} hint="Accepted by a collector and preparing for pickup" />
          <MetricCard label="Completed Requests" value={summary.completed_requests} hint="Fully closed pickups with collection confirmed" />
        </section>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Recent Requests</p>
              <h2 className="mt-2 font-display text-3xl text-ink">Latest pickup activity</h2>
            </div>
            <Link
              to="/dashboard/requests"
              className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm font-semibold text-ink transition hover:border-ink/20"
            >
              Open list
            </Link>
          </div>

          <div className="mt-6 space-y-4">
            {recentRequests.map((request) => (
              <Link
                key={request.id}
                to={`/dashboard/requests/${request.id}`}
                className="block rounded-3xl bg-white/70 p-5 transition hover:-translate-y-0.5 hover:bg-white/80"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.3em] text-ink/45">Request #{request.id}</p>
                    <p className="mt-2 font-semibold text-ink">{request.waste_type}</p>
                  </div>
                  <StatusBadge status={request.status} />
                </div>
                <p className="mt-3 text-sm text-ink/70">{request.address}</p>
                <div className="mt-4 flex flex-wrap gap-6 text-sm text-ink/60">
                  <span>Created: {formatDateTime(request.created_at)}</span>
                  <span>Collector: {request.assigned_collector_name || "Not assigned yet"}</span>
                </div>
              </Link>
            ))}

            {!loading && recentRequests.length === 0 ? (
              <div className="rounded-3xl bg-white/70 p-6">
                <p className="font-display text-2xl text-ink">No requests yet</p>
                <p className="mt-2 text-sm text-ink/70">
                  Create your first pickup request from the form above and it will appear here immediately.
                </p>
              </div>
            ) : null}
          </div>
        </div>

        <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">What You Can Do</p>
          <h2 className="mt-2 font-display text-3xl text-ink">Citizen workflow</h2>
          <div className="mt-6 space-y-4">
            {[
              "Create a request with waste details, photo, and exact address.",
              "Track each status from pending through collection and completion.",
              "Open the details page to review the assigned collector and timeline.",
              "Cancel only while the request is still pending."
            ].map((item) => (
              <div key={item} className="rounded-3xl bg-white/70 p-4 text-sm leading-7 text-ink/75">
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
