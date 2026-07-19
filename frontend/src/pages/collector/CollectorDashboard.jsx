import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";

import { getApiError } from "../../api/errors";
import { Card } from "../../components/ui/card";
import { Skeleton } from "../../components/ui/skeleton";
import { getErrorToast, useToast } from "../../components/ui/toast";
import AvailablePickupList from "../../features/collector/AvailablePickupList";
import AssignedPickupList from "../../features/collector/AssignedPickupList";
import CollectorTimeline from "../../features/collector/CollectorTimeline";
import JobDetailsDialog from "../../features/collector/JobDetailsDialog";
import SummaryCards from "../../features/collector/SummaryCards";
import { useAssignedPickups } from "../../hooks/useAssignedPickups";
import { useBrowserGeolocation } from "../../hooks/useBrowserGeolocation";
import { useCollectorActions } from "../../hooks/useCollectorActions";
import { useCollectorDashboard } from "../../hooks/useCollectorDashboard";
import { useNearbyPickups } from "../../hooks/useNearbyPickups";
import { usePickupRequest } from "../../hooks/usePickupRequests";

const PickupMap = lazy(() => import("../../components/maps/PickupMap"));

function getCoordinate(value) {
  const coordinate = Number(value);
  return Number.isFinite(coordinate) ? coordinate : null;
}

function buildOpenStreetMapDirectionsUrl(collectorLocation, pickup) {
  const pickupLatitude = getCoordinate(pickup?.latitude);
  const pickupLongitude = getCoordinate(pickup?.longitude);

  if (!collectorLocation || pickupLatitude === null || pickupLongitude === null) {
    return "";
  }

  const route = `${collectorLocation.latitude},${collectorLocation.longitude};${pickupLatitude},${pickupLongitude}`;
  const searchParams = new URLSearchParams({
    engine: "fossgis_osrm_car",
    route
  });

  return `https://www.openstreetmap.org/directions?${searchParams.toString()}#map=14/${pickupLatitude}/${pickupLongitude}`;
}

const EMPTY_PICKUPS = [];

export default function CollectorDashboard() {
  const { toast } = useToast();
  const notifiedErrors = useRef(new Set());
  const [busyId, setBusyId] = useState(null);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [selectedMapRequest, setSelectedMapRequest] = useState(null);
  const [completeWeights, setCompleteWeights] = useState({});

  const summaryQuery = useCollectorDashboard();
  const assignedQuery = useAssignedPickups();
  const collectorActions = useCollectorActions();
  const {
    error: collectorLocationError,
    isLocating: isCollectorLocating,
    position: collectorLocation,
    requestLocation: requestCollectorLocation
  } = useBrowserGeolocation({
    watch: true,
    errorTitle: "Collector location unavailable"
  });
  const nearbyQuery = useNearbyPickups(collectorLocation);

  const nearbyPickups = nearbyQuery.data || EMPTY_PICKUPS;
  const assignedJobs = assignedQuery.data || EMPTY_PICKUPS;
  const mappedPickups = useMemo(
    () => [
      ...assignedJobs.map((job) => ({ ...job, map_group: "assigned" })),
      ...nearbyPickups.map((pickup) => ({ ...pickup, map_group: "available" }))
    ],
    [assignedJobs, nearbyPickups]
  );
  const selectedMapPickup =
    mappedPickups.find((pickup) => pickup.id === selectedMapRequest?.id) ||
    mappedPickups[0] ||
    null;
  const recentTimelineRequest = assignedJobs[0] || nearbyPickups[0] || null;
  const timelineQuery = usePickupRequest(recentTimelineRequest?.id);

  const actionError =
    collectorActions.accept.error ||
    collectorActions.start.error ||
    collectorActions.collect.error ||
    collectorActions.complete.error;
  const actionPending =
    collectorActions.accept.isPending ||
    collectorActions.start.isPending ||
    collectorActions.collect.isPending ||
    collectorActions.complete.isPending;

  const actionToastContent = {
    accept: {
      title: "Pickup accepted",
      description: "This request has been added to your assigned jobs."
    },
    start: {
      title: "Journey started",
      description: "The citizen can now see that you are on the way."
    },
    collect: {
      title: "Pickup collected",
      description: "The job is ready for final completion with weight."
    },
    complete: {
      title: "Pickup completed",
      description: "The collected weight has been saved successfully."
    }
  };

  useEffect(() => {
    const errorEntries = [
      ["summary", summaryQuery.error],
      ["nearby", nearbyQuery.error],
      ["assigned", assignedQuery.error],
      ["timeline", timelineQuery.error]
    ];

    errorEntries.forEach(([key, error]) => {
      if (!error) {
        notifiedErrors.current.delete(key);
        return;
      }

      if (notifiedErrors.current.has(key)) {
        return;
      }

      notifiedErrors.current.add(key);
      toast(getErrorToast(error, "Unable to load collector data."));
    });
  }, [assignedQuery.error, nearbyQuery.error, summaryQuery.error, timelineQuery.error, toast]);

  async function runAction(requestId, actionName, payload = {}) {
    setBusyId(requestId);

    try {
      if (actionName === "accept") {
        await collectorActions.accept.mutateAsync(requestId);
      } else if (actionName === "start") {
        await collectorActions.start.mutateAsync(requestId);
      } else if (actionName === "collect") {
        await collectorActions.collect.mutateAsync(requestId);
      } else if (actionName === "complete") {
        await collectorActions.complete.mutateAsync({ id: requestId, weight: payload.weight });
        setCompleteWeights((current) => {
          const next = { ...current };
          delete next[requestId];
          return next;
        });
      }

      if (timelineQuery.data?.id === requestId) {
        await timelineQuery.refetch();
      }

      toast({
        ...actionToastContent[actionName],
        variant: "success"
      });
    } catch (error) {
      toast(getErrorToast(error, "Collector action failed. Please try again."));
    } finally {
      setBusyId(null);
    }
  }

  function handleCompleteWeightChange(requestId, value) {
    setCompleteWeights((current) => ({
      ...current,
      [requestId]: value
    }));
  }

  function handleOpenDetails(request) {
    setSelectedMapRequest(request);
    setSelectedRequest(request);
  }

  function handleDetailsOpenChange(open) {
    if (!open) {
      setSelectedRequest(null);
    }
  }

  function handleNavigateToPickup(request) {
    const pickupLatitude = getCoordinate(request?.latitude);
    const pickupLongitude = getCoordinate(request?.longitude);

    if (pickupLatitude === null || pickupLongitude === null) {
      toast({
        title: "Pickup location unavailable",
        description: "This pickup does not have valid coordinates for navigation.",
        variant: "error"
      });
      return;
    }

    if (!collectorLocation) {
      requestCollectorLocation();
      toast({
        title: "Collector location needed",
        description: "Allow location access, then tap Navigate again.",
        variant: "error"
      });
      return;
    }

    window.open(buildOpenStreetMapDirectionsUrl(collectorLocation, request), "_blank", "noopener,noreferrer");
  }

  const timelineRequest = timelineQuery.data || recentTimelineRequest;

  return (
    <div className="space-y-6">
      <Suspense fallback={<p className="text-sm text-ink/70">Loading collector map...</p>}>
        <PickupMap
          pickups={mappedPickups}
          collectorLocation={collectorLocation}
          collectorLocationError={collectorLocationError}
          collectorLocationLoading={isCollectorLocating}
          onRetryCollectorLocation={requestCollectorLocation}
          showCollectorLocation
          selectedPickupId={selectedMapPickup?.id}
          onPickupSelect={setSelectedMapRequest}
          title="Collector live map"
          description={`${assignedJobs.length} assigned jobs and ${nearbyPickups.length} available nearby jobs.`}
          useBrowserCollectorLocation={false}
        />
      </Suspense>

      <SummaryCards
        summary={summaryQuery.data}
        loading={summaryQuery.isPending}
        error={summaryQuery.error}
      />

      {actionError ? (
        <Card className="border-coral/30 bg-coral/10 p-4" role="alert">
          <p className="text-sm font-semibold text-coral">
            {getApiError(actionError, "Collector action failed. Please try again.")}
          </p>
        </Card>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Nearby Pickups</p>
            <h2 className="mt-2 font-display text-3xl text-ink">Open requests near you</h2>
          </div>
          {isCollectorLocating && !collectorLocation ? (
            <Card className="p-5">
              <Skeleton className="h-4 w-40 rounded-full bg-leaf/15" />
              <Skeleton className="mt-4 h-20 rounded-2xl bg-white/60" />
            </Card>
          ) : (
            <AvailablePickupList
              pickups={nearbyPickups}
              loading={nearbyQuery.isPending && Boolean(collectorLocation)}
              error={nearbyQuery.error}
              busyId={busyId}
              actionDisabled={actionPending}
              onAccept={(requestId) => runAction(requestId, "accept")}
              onViewDetails={handleOpenDetails}
              onSelectPickup={setSelectedMapRequest}
              selectedPickupId={selectedMapPickup?.id}
              emptyTitle={collectorLocation ? "No nearby pickups" : "Share location to find nearby pickups"}
              emptyDescription={
                collectorLocation
                  ? "No open pickup requests were found within 5 km."
                  : "Allow browser location access to load nearby pickup requests."
              }
              renderFooterSlot={(pickup) => (
                <span className="inline-flex items-center rounded-2xl bg-white/80 px-4 py-2.5 text-sm font-semibold text-ink/70">
                  {pickup.distance_km} km away
                </span>
              )}
            />
          )}
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Assigned Jobs</p>
            <h2 className="mt-2 font-display text-3xl text-ink">My collection work</h2>
          </div>
          <AssignedPickupList
            jobs={assignedJobs}
            loading={assignedQuery.isPending}
            error={assignedQuery.error}
            busyId={busyId}
            actionDisabled={actionPending}
            completeWeights={completeWeights}
            onStart={(requestId) => runAction(requestId, "start")}
            onCollect={(requestId) => runAction(requestId, "collect")}
            onComplete={(requestId, weight) => runAction(requestId, "complete", { weight })}
            onCompleteWeightChange={handleCompleteWeightChange}
            onViewDetails={handleOpenDetails}
            onNavigate={handleNavigateToPickup}
            onSelectPickup={setSelectedMapRequest}
            selectedPickupId={selectedMapPickup?.id}
            navigationLoading={isCollectorLocating}
          />
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Recent Timeline</p>
          <h2 className="mt-2 font-display text-3xl text-ink">Latest pickup movement</h2>
        </div>
        <Card className="p-5">
          {timelineRequest ? (
            <CollectorTimeline
              timeline={timelineRequest.timeline || []}
              currentStatus={timelineRequest.status}
              loading={timelineQuery.isFetching}
              emptyMessage="Timeline events will appear here as this collector job moves forward."
            />
          ) : (
            <div className="rounded-3xl border border-dashed border-ink/10 bg-white/65 p-5">
              <p className="font-display text-2xl text-ink">No recent timeline yet</p>
              <p className="mt-2 text-sm leading-6 text-ink/70">
                Accept a pickup request and its timeline will appear here.
              </p>
            </div>
          )}
        </Card>
      </section>

      <JobDetailsDialog
        request={selectedRequest}
        open={Boolean(selectedRequest)}
        onOpenChange={handleDetailsOpenChange}
        showTrigger={false}
        timeline={selectedRequest?.id === timelineRequest?.id ? timelineRequest?.timeline || [] : []}
        timelineLoading={selectedRequest?.id === timelineRequest?.id ? timelineQuery.isFetching : false}
        busy={selectedRequest ? busyId === selectedRequest.id : false}
        actionDisabled={actionPending}
        completeWeight={selectedRequest ? (completeWeights[selectedRequest.id] ?? "") : ""}
        onAccept={(requestId) => runAction(requestId, "accept")}
        onStart={(requestId) => runAction(requestId, "start")}
        onCollect={(requestId) => runAction(requestId, "collect")}
        onComplete={(requestId, weight) => runAction(requestId, "complete", { weight })}
        onCompleteWeightChange={handleCompleteWeightChange}
      />
    </div>
  );
}
