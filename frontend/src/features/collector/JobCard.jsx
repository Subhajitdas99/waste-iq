import { CalendarClock, Eye, MapPin, Navigation, Package, Scale, User, Weight } from "lucide-react";

import StatusBadge from "../../components/StatusBadge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../components/ui/card";
import { Skeleton } from "../../components/ui/skeleton";
import { formatDateTime } from "../../utils/pickupRequests";

export const collectorJobActions = {
  pending: {
    label: "Accept",
    action: "accept"
  },
  accepted: {
    label: "Start Journey",
    action: "start"
  },
  on_the_way: {
    label: "Collected",
    action: "collect"
  },
  collected: {
    label: "Complete",
    action: "complete"
  }
};

export function CollectorDetailField({ label, value, icon: Icon }) {
  return (
    <div className="rounded-2xl bg-white/60 px-4 py-3">
      <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-ink/45">
        {Icon ? <Icon className="h-3.5 w-3.5" /> : null}
        {label}
      </p>
      <p className="mt-1 text-sm font-medium text-ink">{value || "Not available"}</p>
    </div>
  );
}

export function JobListSkeleton({ count = 4, label = "Loading collector pickup jobs" }) {
  return (
    <section className="grid gap-4 lg:grid-cols-2" aria-label={label}>
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index} className="p-5">
          <Skeleton className="h-3 w-28 rounded-full bg-leaf/15" />
          <Skeleton className="mt-4 h-8 w-48 rounded-2xl" />
          <Skeleton className="mt-5 h-16 w-full rounded-2xl" />
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <Skeleton className="h-12 rounded-2xl bg-white/60" />
            <Skeleton className="h-12 rounded-2xl bg-white/60" />
          </div>
        </Card>
      ))}
    </section>
  );
}

function getWeightValue(weight) {
  if (weight === null || weight === undefined || weight === "") {
    return "";
  }

  return String(weight);
}

export default function JobCard({
  request,
  busy = false,
  onAccept,
  onStart,
  onCollect,
  onComplete,
  onViewDetails,
  completeWeight = "",
  onCompleteWeightChange,
  actionDisabled = false,
  showDetailsAction = true,
  footerSlot = null
}) {
  const action = collectorJobActions[request?.status];
  const isCollected = request?.status === "collected";
  const weightValue = getWeightValue(completeWeight);
  const parsedWeight = Number(weightValue);
  const canSubmitWeight = Number.isFinite(parsedWeight) && parsedWeight > 0;
  const hasActionHandler =
    (action?.action === "accept" && Boolean(onAccept)) ||
    (action?.action === "start" && Boolean(onStart)) ||
    (action?.action === "collect" && Boolean(onCollect)) ||
    (action?.action === "complete" && Boolean(onComplete));

  function handlePrimaryAction() {
    if (!request || !action) {
      return;
    }

    if (action.action === "accept") {
      onAccept?.(request.id, request);
    } else if (action.action === "start") {
      onStart?.(request.id, request);
    } else if (action.action === "collect") {
      onCollect?.(request.id, request);
    } else if (canSubmitWeight) {
      onComplete?.(request.id, parsedWeight, request);
    }
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-leaf/70">
              Request #{request?.id}
            </p>
            <CardTitle className="mt-2 flex items-center gap-2">
              <Package className="h-5 w-5 text-leaf" />
              {request?.waste_type || "Pickup request"}
            </CardTitle>
          </div>
          {request?.status ? <StatusBadge status={request.status} /> : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <CollectorDetailField label="Citizen" value={request?.citizen_name} />
          <CollectorDetailField label="Created" value={formatDateTime(request?.created_at)} />
        </div>

        <div className="rounded-2xl bg-white/60 px-4 py-3">
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-ink/45">
            <MapPin className="h-3.5 w-3.5" />
            Address
          </p>
          <p className="mt-2 text-sm leading-6 text-ink/75">{request?.address || "Not available"}</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <CollectorDetailField label="Latitude" value={request?.latitude} />
          <CollectorDetailField label="Longitude" value={request?.longitude} />
        </div>

        {request?.assignment?.weight_kg ? (
          <div className="flex items-center gap-2 rounded-2xl bg-leaf/10 px-4 py-3 text-sm font-semibold text-leaf">
            <Scale className="h-4 w-4" />
            {request.assignment.weight_kg} kg collected
          </div>
        ) : null}

        {isCollected ? (
          <label className="block">
            <span className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-ink/45">
              <Weight className="h-3.5 w-3.5" />
              Completion weight
            </span>
            <input
              type="number"
              min="0.1"
              step="0.1"
              value={weightValue}
              onChange={(event) => onCompleteWeightChange?.(request.id, event.target.value, request)}
              placeholder="Weight (kg)"
              className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-leaf"
            />
          </label>
        ) : null}
      </CardContent>

      <CardFooter className="flex flex-wrap gap-3">
        {action && hasActionHandler ? (
          <button
            type="button"
            onClick={handlePrimaryAction}
            disabled={busy || actionDisabled || (isCollected && !canSubmitWeight)}
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-ink px-4 py-2.5 text-sm font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
          >
            {action.action === "start" || action.action === "collect" ? <Navigation className="h-4 w-4" /> : null}
            {busy ? "Working..." : action.label}
          </button>
        ) : null}

        {showDetailsAction ? (
          <button
            type="button"
            onClick={() => onViewDetails?.(request)}
            className="inline-flex items-center justify-center gap-2 rounded-2xl border border-ink/10 bg-white/80 px-4 py-2.5 text-sm font-semibold text-ink transition hover:border-ink/20"
          >
            <Eye className="h-4 w-4" />
            View details
          </button>
        ) : null}

        {footerSlot}
      </CardFooter>

      <div className="flex flex-wrap gap-3 border-t border-white/60 px-5 py-4 text-xs font-semibold uppercase tracking-[0.22em] text-ink/45">
        <span className="inline-flex items-center gap-2">
          <User className="h-3.5 w-3.5" />
          {request?.assigned_collector_name || "Collector pending"}
        </span>
        <span className="inline-flex items-center gap-2">
          <CalendarClock className="h-3.5 w-3.5" />
          {formatDateTime(request?.created_at)}
        </span>
      </div>
    </Card>
  );
}
