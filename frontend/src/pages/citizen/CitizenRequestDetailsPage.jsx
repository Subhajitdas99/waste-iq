import { ArrowLeft, MapPinned, RefreshCw, Truck, XCircle } from "lucide-react";
import { Link, Navigate, useParams } from "react-router-dom";

import { getApiError } from "../../api/errors";
import RequestTimeline from "../../components/citizen/RequestTimeline";
import StatusBadge from "../../components/StatusBadge";
import { getErrorToast, useToast } from "../../components/ui/toast";
import { useAuth } from "../../hooks/useAuth";
import { useCancelPickup, usePickupRequest } from "../../hooks/usePickupRequests";
import { formatDateTime } from "../../utils/pickupRequests";

export default function CitizenRequestDetailsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const { requestId } = useParams();
  const {
    data: request,
    error: requestError,
    isLoading: loading,
    refetch: loadRequest
  } = usePickupRequest(requestId);
  const cancelPickup = useCancelPickup();
  const busy = cancelPickup.isPending;
  const error = requestError
    ? getApiError(requestError, "Unable to load this pickup request.")
    : cancelPickup.error
      ? getApiError(cancelPickup.error, "Unable to cancel this pickup request.")
      : "";

  async function handleCancel() {
    try {
      await cancelPickup.mutateAsync(requestId);
      toast({
        title: "Pickup cancelled",
        description: "Your pickup request has been cancelled.",
        variant: "success"
      });
    } catch (err) {
      toast(getErrorToast(err, "Unable to cancel this pickup request."));
    }
  }

  if (user?.role !== "citizen") {
    return <Navigate to="/dashboard" replace />;
  }

  if (loading && !request) {
    return <p className="text-sm text-ink/70">Loading request details...</p>;
  }

  return (
    <div className="space-y-6">
      {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      {request ? (
        <>
          <section className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <Link
                  to="/dashboard/requests"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-ink/65 transition hover:text-ink"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to my requests
                </Link>
                <p className="mt-5 text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Request #{request.id}</p>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <h2 className="font-display text-4xl text-ink">{request.waste_type}</h2>
                  <StatusBadge status={request.status} />
                </div>
                <p className="mt-4 max-w-3xl text-sm leading-7 text-ink/70">{request.address}</p>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => loadRequest()}
                  className="inline-flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm font-semibold text-ink transition hover:border-ink/20"
                >
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </button>
                {request.can_cancel ? (
                  <button
                    type="button"
                    onClick={handleCancel}
                    disabled={busy}
                    className="inline-flex items-center gap-2 rounded-2xl bg-rose-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-rose-600 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <XCircle className="h-4 w-4" />
                    {busy ? "Cancelling..." : "Cancel request"}
                  </button>
                ) : null}
              </div>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <div className="space-y-6">
              <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Full Information</p>
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-3xl bg-white/70 p-4">
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Created Date</p>
                    <p className="mt-2 font-semibold text-ink">{formatDateTime(request.created_at)}</p>
                  </div>
                  <div className="rounded-3xl bg-white/70 p-4">
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Assigned Collector</p>
                    <p className="mt-2 font-semibold text-ink">{request.assigned_collector_name || "Not assigned yet"}</p>
                  </div>
                  <div className="rounded-3xl bg-white/70 p-4">
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Latitude</p>
                    <p className="mt-2 font-semibold text-ink">{request.latitude}</p>
                  </div>
                  <div className="rounded-3xl bg-white/70 p-4">
                    <p className="text-xs uppercase tracking-[0.28em] text-ink/45">Longitude</p>
                    <p className="mt-2 font-semibold text-ink">{request.longitude}</p>
                  </div>
                </div>

                <div className="mt-5 rounded-[2rem] bg-white/70 p-5">
                  <div className="flex items-center gap-3 text-ink">
                    <MapPinned className="h-5 w-5 text-leaf" />
                    <p className="font-semibold">Pickup address</p>
                  </div>
                  <p className="mt-3 text-sm leading-7 text-ink/75">{request.address}</p>
                </div>

                <div className="mt-5 rounded-[2rem] bg-white/70 p-5">
                  <div className="flex items-center gap-3 text-ink">
                    <Truck className="h-5 w-5 text-leaf" />
                    <p className="font-semibold">Collector assignment</p>
                  </div>
                  <p className="mt-3 text-sm leading-7 text-ink/75">
                    {request.assigned_collector_name
                      ? `${request.assigned_collector_name} accepted this request and will continue updating the timeline as the pickup progresses.`
                      : "No collector has been assigned to this request yet. It remains visible in the pending queue."}
                  </p>
                </div>

                {request.photo_url ? (
                  <div className="mt-5">
                    <img
                      src={request.photo_url}
                      alt={request.waste_type}
                      className="h-80 w-full rounded-[2rem] object-cover shadow-glow"
                    />
                  </div>
                ) : null}
              </div>
            </div>

            <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Timeline</p>
              <h3 className="mt-2 font-display text-3xl text-ink">Pickup journey</h3>
              <p className="mt-2 text-sm text-ink/70">
                Every status change is logged here so you can tell exactly where your request stands.
              </p>
              <div className="mt-6">
                <RequestTimeline timeline={request.timeline} currentStatus={request.status} />
              </div>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
