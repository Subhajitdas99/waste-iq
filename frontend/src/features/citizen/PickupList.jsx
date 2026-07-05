import { Eye, XCircle } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { getApiError } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../components/ui/card";
import { Skeleton } from "../../components/ui/skeleton";
import { getErrorToast, useToast } from "../../components/ui/toast";
import { useCancelPickup, usePickupRequests } from "../../hooks/usePickupRequests";
import { formatDateTime } from "../../utils/pickupRequests";

function PickupListSkeleton() {
  return (
    <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3" aria-label="Loading pickup requests">
      {Array.from({ length: 3 }).map((_, index) => (
        <Card key={index} className="p-5">
          <Skeleton className="h-3 w-28 rounded-full bg-leaf/15" />
          <Skeleton className="mt-4 h-8 w-40 rounded-2xl" />
          <Skeleton className="mt-5 h-3 w-full rounded-full" />
          <Skeleton className="mt-2 h-3 w-4/5 rounded-full" />
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <Skeleton className="h-12 rounded-2xl bg-sand/70" />
            <Skeleton className="h-12 rounded-2xl bg-sand/70" />
          </div>
        </Card>
      ))}
    </section>
  );
}

function Field({ label, value }) {
  return (
    <div className="rounded-2xl bg-white/60 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-ink/45">{label}</p>
      <p className="mt-1 text-sm font-medium text-ink">{value}</p>
    </div>
  );
}

export default function PickupList() {
  const { data: requests = [], error, isError, isPending } = usePickupRequests();
  const cancelPickup = useCancelPickup();
  const { toast } = useToast();
  const [cancelError, setCancelError] = useState("");
  const [cancellingId, setCancellingId] = useState(null);

  async function handleCancel(requestId) {
    setCancelError("");
    setCancellingId(requestId);

    try {
      await cancelPickup.mutateAsync(requestId);
      toast({
        title: "Pickup cancelled",
        description: "Your pickup request has been cancelled.",
        variant: "success"
      });
    } catch (err) {
      setCancelError(getApiError(err, "Unable to cancel this pickup request."));
      toast(getErrorToast(err, "Unable to cancel this pickup request."));
    } finally {
      setCancellingId(null);
    }
  }

  if (isPending) {
    return <PickupListSkeleton />;
  }

  if (isError) {
    return (
      <Card className="border-coral/30 bg-coral/10 p-5" role="alert">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-coral">
          {!error?.response ? "No internet" : "Requests unavailable"}
        </p>
        <p className="mt-3 text-sm text-ink/70">
          {!error?.response
            ? "No internet connection. Reconnect and refresh to load your pickup requests."
            : getApiError(error, "Unable to load your pickup requests.")}
        </p>
      </Card>
    );
  }

  if (requests.length === 0) {
    return (
      <Card className="p-6">
        <p className="font-display text-2xl text-ink">No pickup requests yet</p>
        <p className="mt-2 text-sm text-ink/70">
          Create your first pickup request and it will appear here with live status updates.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {cancelError ? (
        <Card className="border-coral/30 bg-coral/10 p-4" role="alert">
          <p className="text-sm font-medium text-coral">{cancelError}</p>
        </Card>
      ) : null}

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3" aria-label="Pickup requests">
        {requests.map((request) => (
          <Card key={request.id} className="overflow-hidden">
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">
                    Request #{request.id}
                  </p>
                  <CardTitle className="mt-2">{request.waste_type}</CardTitle>
                </div>
                <StatusBadge status={request.status} />
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <Field label="Address" value={request.address} />
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Created Date" value={formatDateTime(request.created_at)} />
                <Field label="Assigned Collector" value={request.assigned_collector_name || "Not assigned yet"} />
              </div>
            </CardContent>

            <CardFooter className="flex-wrap gap-3">
              <Link
                to={`/dashboard/requests/${request.id}`}
                className="inline-flex items-center gap-2 rounded-2xl border border-ink/10 bg-white/80 px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink/20"
              >
                <Eye className="h-4 w-4" />
                View
              </Link>
              {request.can_cancel ? (
                <button
                  type="button"
                  onClick={() => handleCancel(request.id)}
                  disabled={cancellingId === request.id}
                  className="inline-flex items-center gap-2 rounded-2xl bg-coral px-4 py-2 text-sm font-semibold text-ink transition hover:bg-ember disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <XCircle className="h-4 w-4" />
                  {cancellingId === request.id ? "Cancelling..." : "Cancel"}
                </button>
              ) : null}
            </CardFooter>
          </Card>
        ))}
      </section>
    </div>
  );
}
