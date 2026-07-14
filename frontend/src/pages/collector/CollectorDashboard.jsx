import { useEffect, useRef, useState } from "react";

import { getApiError } from "../../api/errors";
import { Card } from "../../components/ui/card";
import { getErrorToast, useToast } from "../../components/ui/toast";
import AvailablePickupList from "../../features/collector/AvailablePickupList";
import AssignedPickupList from "../../features/collector/AssignedPickupList";
import CollectorTimeline from "../../features/collector/CollectorTimeline";
import JobDetailsDialog from "../../features/collector/JobDetailsDialog";
import SummaryCards from "../../features/collector/SummaryCards";
import { useAvailablePickups } from "../../hooks/useAvailablePickups";
import { useAssignedPickups } from "../../hooks/useAssignedPickups";
import { useCollectorActions } from "../../hooks/useCollectorActions";
import { useCollectorDashboard } from "../../hooks/useCollectorDashboard";
import { usePickupRequest } from "../../hooks/usePickupRequests";

export default function CollectorDashboard() {
  const { toast } = useToast();
  const notifiedErrors = useRef(new Set());
  const [busyId, setBusyId] = useState(null);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [completeWeights, setCompleteWeights] = useState({});

  const summaryQuery = useCollectorDashboard();
  const availableQuery = useAvailablePickups();
  const assignedQuery = useAssignedPickups();
  const collectorActions = useCollectorActions();

  const availablePickups = availableQuery.data || [];
  const assignedJobs = assignedQuery.data || [];
  const recentTimelineRequest = assignedJobs[0] || availablePickups[0] || null;
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
      ["available", availableQuery.error],
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
  }, [availableQuery.error, assignedQuery.error, summaryQuery.error, timelineQuery.error, toast]);

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
    setSelectedRequest(request);
  }

  function handleDetailsOpenChange(open) {
    if (!open) {
      setSelectedRequest(null);
    }
  }

  const timelineRequest = timelineQuery.data || recentTimelineRequest;

  return (
    <div className="space-y-6">
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
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Available Pickups</p>
            <h2 className="mt-2 font-display text-3xl text-ink">Open request queue</h2>
          </div>
          <AvailablePickupList
            pickups={availablePickups}
            loading={availableQuery.isPending}
            error={availableQuery.error}
            busyId={busyId}
            actionDisabled={actionPending}
            onAccept={(requestId) => runAction(requestId, "accept")}
            onViewDetails={handleOpenDetails}
            emptyDescription="Check back soon for new requests in Kolkata."
          />
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
