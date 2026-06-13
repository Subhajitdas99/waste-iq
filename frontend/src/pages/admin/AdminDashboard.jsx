import { useEffect, useState } from "react";

import api, { getApiError } from "../../api/client";
import MetricCard from "../../components/MetricCard";
import StatusBadge from "../../components/StatusBadge";

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      const [analyticsResponse, usersResponse, requestsResponse] = await Promise.all([
        api.get("/admin/analytics"),
        api.get("/admin/users"),
        api.get("/pickup-requests")
      ]);

      setAnalytics(analyticsResponse.data);
      setUsers(usersResponse.data);
      setRequests(requestsResponse.data);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Unable to load admin dashboard."));
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (!analytics && !error) {
    return <p className="text-sm text-ink/70">Loading dashboard metrics...</p>;
  }

  return (
    <div className="space-y-8">
      {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      {analytics ? (
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Users" value={analytics.total_users} hint="All registered citizens, collectors, and admins" />
          <MetricCard label="Pickup Requests" value={analytics.total_pickup_requests} hint="Created across the marketplace" />
          <MetricCard label="Completed" value={analytics.total_completed_pickups} hint="Pickups completed by collectors" />
          <MetricCard label="Collected Weight" value={`${analytics.total_collected_weight_kg} kg`} hint="Total reported recyclable weight" />
        </section>
      ) : null}

      {analytics ? (
        <section className="grid gap-5 lg:grid-cols-2">
          <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Users by role</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              <MetricCard label="Citizens" value={analytics.users_by_role.citizens} hint="Waste suppliers" />
              <MetricCard label="Collectors" value={analytics.users_by_role.collectors} hint="Pickup operators" />
              <MetricCard label="Admins" value={analytics.users_by_role.admins} hint="Ops access" />
            </div>
          </div>
          <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Requests by status</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              {Object.entries(analytics.requests_by_status).map(([status, count]) => (
                <div key={status} className="rounded-3xl bg-white/70 p-5">
                  <StatusBadge status={status} />
                  <p className="mt-4 font-display text-4xl text-ink">{count}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      ) : null}

      <section className="grid gap-8 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Users</p>
              <h2 className="mt-2 font-display text-3xl text-ink">Platform accounts</h2>
            </div>
            <button
              type="button"
              onClick={loadDashboard}
              className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm font-semibold text-ink"
            >
              Refresh
            </button>
          </div>

          <div className="space-y-3">
            {users.map((user) => (
              <div key={user.id} className="rounded-3xl bg-white/70 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold text-ink">{user.name}</p>
                    <p className="text-sm text-ink/70">{user.email}</p>
                  </div>
                  <StatusBadge status={user.role} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Requests</p>
          <h2 className="mt-2 font-display text-3xl text-ink">Pickup request feed</h2>

          <div className="mt-6 space-y-4">
            {requests.map((request) => (
              <div key={request.id} className="rounded-3xl bg-white/70 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-semibold text-ink">{request.waste_type}</p>
                    <p className="text-sm text-ink/70">{request.citizen_name}</p>
                    <p className="text-sm text-ink/60">{request.address}</p>
                  </div>
                  <StatusBadge status={request.status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
