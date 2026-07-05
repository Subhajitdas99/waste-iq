import { useState } from "react";

import { getApiError } from "../../api/errors";
import MetricCard from "../../components/MetricCard";
import StatusBadge from "../../components/StatusBadge";
import {
  useAdminAnalytics,
  useAdminDealers,
  useAdminUsers,
  useApproveDealer,
  usePickupRequests,
  useRejectDealer
} from "../../hooks/usePickupRequests";
import { formatDateTime } from "../../utils/pickupRequests";

export default function AdminDashboard() {
  const [busyDealerId, setBusyDealerId] = useState(null);
  const analyticsQuery = useAdminAnalytics();
  const usersQuery = useAdminUsers();
  const dealersQuery = useAdminDealers();
  const requestsQuery = usePickupRequests();
  const approveDealer = useApproveDealer();
  const rejectDealer = useRejectDealer();

  const analytics = analyticsQuery.data;
  const dealers = dealersQuery.data || [];
  const users = usersQuery.data || [];
  const requests = requestsQuery.data || [];
  const loadError = analyticsQuery.error || usersQuery.error || requestsQuery.error || dealersQuery.error;
  const dealerActionError = approveDealer.error || rejectDealer.error;
  const error = dealerActionError
    ? getApiError(dealerActionError, "Unable to update dealer verification status.")
    : loadError
      ? getApiError(loadError, "Unable to load admin dashboard.")
      : "";

  async function loadDashboard() {
    await Promise.all([
      analyticsQuery.refetch(),
      usersQuery.refetch(),
      requestsQuery.refetch(),
      dealersQuery.refetch()
    ]);
  }

  async function handleDealerAction(dealerUserId, action) {
    setBusyDealerId(dealerUserId);
    try {
      if (action === "approve") {
        await approveDealer.mutateAsync(dealerUserId);
      } else {
        await rejectDealer.mutateAsync(dealerUserId);
      }
      await loadDashboard();
    } catch {
      // Error state is read from the dealer mutation.
    } finally {
      setBusyDealerId(null);
    }
  }

  if (!analytics && !error) {
    return <p className="text-sm text-ink/70">Loading dashboard metrics...</p>;
  }

  return (
    <div className="space-y-8">
      {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      {analytics ? (
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Users" value={analytics.total_users} hint="All registered citizens, collectors, dealers, and admins" />
          <MetricCard label="Pickup Requests" value={analytics.total_pickup_requests} hint="Created across the marketplace" />
          <MetricCard label="Completed" value={analytics.total_completed_pickups} hint="Pickups completed by collectors" />
          <MetricCard label="Collected Weight" value={`${analytics.total_collected_weight_kg} kg`} hint="Total reported recyclable weight" />
        </section>
      ) : null}

      {analytics ? (
        <section className="grid gap-5 lg:grid-cols-2">
          <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Users by role</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Citizens" value={analytics.users_by_role.citizens} hint="Waste suppliers" />
              <MetricCard label="Collectors" value={analytics.users_by_role.collectors} hint="Pickup operators" />
              <MetricCard label="Dealers" value={analytics.users_by_role.dealers} hint="Buyer accounts" />
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

      <section className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Dealer Verification</p>
            <h2 className="mt-2 font-display text-3xl text-ink">Dealer onboarding review</h2>
            <p className="mt-2 text-sm text-ink/70">
              Review submitted dealer business profiles and move them between pending, approved, and rejected states.
            </p>
          </div>
          <button
            type="button"
            onClick={loadDashboard}
            className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm font-semibold text-ink"
          >
            Refresh
          </button>
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          {dealers.map((dealer) => (
            <div key={dealer.user_id} className="rounded-[2rem] bg-white/70 p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-ink">{dealer.user_name}</p>
                  <p className="text-sm text-ink/70">{dealer.user_email}</p>
                  <p className="text-sm text-ink/60">{dealer.account_phone}</p>
                </div>
                <StatusBadge status={dealer.verification_status} />
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <div className="rounded-3xl bg-white/80 p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Business</p>
                  <p className="mt-2 font-semibold text-ink">{dealer.business_name || "Profile not submitted yet"}</p>
                  <p className="mt-1 text-sm text-ink/70">{dealer.owner_name || "Awaiting dealer submission"}</p>
                </div>
                <div className="rounded-3xl bg-white/80 p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Coverage</p>
                  <p className="mt-2 font-semibold text-ink">{dealer.city || "Unknown city"}</p>
                  <p className="mt-1 text-sm text-ink/70">{dealer.pincode || "No pincode yet"}</p>
                </div>
                <div className="rounded-3xl bg-white/80 p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Profile completion</p>
                  <p className="mt-2 font-display text-3xl text-ink">{dealer.profile_completion}%</p>
                </div>
                <div className="rounded-3xl bg-white/80 p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Approval date</p>
                  <p className="mt-2 font-semibold text-ink">
                    {dealer.approved_at ? formatDateTime(dealer.approved_at) : "Not approved yet"}
                  </p>
                </div>
              </div>

              <div className="mt-5 rounded-3xl bg-white/80 p-4">
                <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Materials accepted</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {dealer.materials_accepted.length > 0 ? (
                    dealer.materials_accepted.map((item) => (
                      <span key={item} className="rounded-full bg-white px-3 py-2 text-sm font-medium text-ink shadow-sm">
                        {item}
                      </span>
                    ))
                  ) : (
                    <p className="text-sm text-ink/65">Dealer has not submitted the profile yet.</p>
                  )}
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={!dealer.has_profile || dealer.verification_status === "approved" || busyDealerId === dealer.user_id}
                  onClick={() => handleDealerAction(dealer.user_id, "approve")}
                  className="rounded-2xl bg-leaf px-4 py-3 text-sm font-semibold text-sand transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busyDealerId === dealer.user_id ? "Updating..." : "Approve dealer"}
                </button>
                <button
                  type="button"
                  disabled={!dealer.has_profile || dealer.verification_status === "rejected" || busyDealerId === dealer.user_id}
                  onClick={() => handleDealerAction(dealer.user_id, "reject")}
                  className="rounded-2xl bg-rose-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-rose-600 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busyDealerId === dealer.user_id ? "Updating..." : "Reject dealer"}
                </button>
              </div>
            </div>
          ))}

          {dealers.length === 0 ? (
            <div className="rounded-[2rem] bg-white/70 p-6">
              <p className="font-display text-2xl text-ink">No dealer accounts yet</p>
              <p className="mt-2 text-sm text-ink/70">
                Dealer role users and their verification profiles will appear here once registrations start.
              </p>
            </div>
          ) : null}
        </div>
      </section>

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
