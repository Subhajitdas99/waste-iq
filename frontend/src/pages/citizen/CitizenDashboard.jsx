import { ArrowRight } from "lucide-react";
import { lazy, Suspense, useState } from "react";
import { Link } from "react-router-dom";

import CreatePickupForm from "../../features/citizen/CreatePickupForm";
import PickupList from "../../features/citizen/PickupList";
import PickupTimeline from "../../features/citizen/PickupTimeline";
import SummaryCards from "../../features/citizen/SummaryCards";
import { Skeleton } from "../../components/ui/skeleton";
import { usePickupRequests } from "../../hooks/usePickupRequests";

const PickupMap = lazy(() => import("../../components/maps/PickupMap"));

function TimelinePanel({ requests = [], error = null, isError = false, isPending = false }) {
  const [selectedRequestId, setSelectedRequestId] = useState(null);
  const activeRequestId = selectedRequestId || requests[0]?.id;

  return (
    <section className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Pickup Timeline</p>
          <h2 className="mt-2 font-display text-3xl text-ink">Review request journey</h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-ink/70">
            Select a pickup request and open the timeline to inspect every transition from request creation to completion.
          </p>
        </div>

        {activeRequestId ? <PickupTimeline requestId={activeRequestId} triggerLabel="Open Timeline" /> : null}
      </div>

      {isPending ? (
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-16 rounded-2xl bg-white/60" />
          ))}
        </div>
      ) : null}

      {isError ? (
        <div className="mt-6 rounded-3xl border border-coral/30 bg-coral/10 p-5" role="alert">
          <p className="font-display text-2xl text-coral">{!error?.response ? "No internet" : "Timeline unavailable"}</p>
          <p className="mt-2 text-sm leading-6 text-ink/70">
            {!error?.response
              ? "No internet connection. Reconnect to choose a pickup timeline."
              : "Unable to load your pickup requests for the timeline selector."}
          </p>
        </div>
      ) : null}

      {!isPending && !isError && requests.length > 0 ? (
        <div className="mt-6 flex gap-3 overflow-x-auto pb-1">
          {requests.map((request) => (
            <button
              key={request.id}
              type="button"
              onClick={() => setSelectedRequestId(request.id)}
              className={`min-w-[13rem] rounded-2xl px-4 py-3 text-left text-sm transition ${
                activeRequestId === request.id
                  ? "bg-ink text-sand shadow-glow"
                  : "border border-ink/10 bg-white/70 text-ink hover:border-ink/20"
              }`}
            >
              <span className="block text-xs font-semibold uppercase tracking-[0.25em] opacity-70">
                Request #{request.id}
              </span>
              <span className="mt-2 block truncate font-semibold">{request.waste_type}</span>
            </button>
          ))}
        </div>
      ) : null}

      {!isPending && !isError && requests.length === 0 ? (
        <div className="mt-6 rounded-3xl bg-white/70 p-5">
          <p className="font-display text-2xl text-ink">No timeline yet</p>
          <p className="mt-2 text-sm text-ink/70">
            Create a pickup request first, then its timeline will appear here.
          </p>
        </div>
      ) : null}
    </section>
  );
}

export default function CitizenDashboard() {
  const pickupRequestsQuery = usePickupRequests();
  const requests = pickupRequestsQuery.data || [];

  return (
    <div className="space-y-8">
      <SummaryCards />

      <section className="glass-panel overflow-hidden rounded-[2rem] border border-white/60 shadow-glow">
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
          </div>
        </div>
      </section>

      <Suspense fallback={<p className="text-sm text-ink/70">Loading pickup map...</p>}>
        <PickupMap
          pickups={requests}
          title="Your pickup map"
          description="See your pickup requests by location and status."
        />
      </Suspense>

      <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">My Requests</p>
            <h2 className="mt-2 font-display text-3xl text-ink">Pickup request board</h2>
          </div>
          <PickupList
            requests={requests}
            error={pickupRequestsQuery.error}
            isError={pickupRequestsQuery.isError}
            isPending={pickupRequestsQuery.isPending}
          />
        </div>

        <div>
          <CreatePickupForm />
        </div>
      </section>

      <TimelinePanel
        requests={requests}
        error={pickupRequestsQuery.error}
        isError={pickupRequestsQuery.isError}
        isPending={pickupRequestsQuery.isPending}
      />
    </div>
  );
}
