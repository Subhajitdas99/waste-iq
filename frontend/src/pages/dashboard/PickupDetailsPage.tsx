import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertCircle, AlertTriangle, ArrowLeft, CheckCircle2, Clock3, HelpCircle, Info, MapPinned, PhoneCall, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { ProgressTracker } from "@/components/dashboard/ProgressTracker";
import { Timeline } from "@/components/dashboard/Timeline";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { ConfirmationDialog } from "@/components/dashboard/ConfirmationDialog";
import { MaskedContactModal } from "@/components/dashboard/MaskedContactModal";
import { Modal } from "@/components/Modal";
import {
  useCancelCitizenPickup,
  useCitizenPickupDetail,
  useConfirmPickupWeight,
  useDisputePickupWeight,
} from "@/hooks/useCitizenPickups";
import { getApiErrorMessage } from "@/lib/api-error";
import { formatDateTime, formatWeight } from "@/lib/pickup";

export function PickupDetailsPage() {
  const params = useParams();
  const requestId = Number(params.id ?? 0);
  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  const [isDisputeModalOpen, setIsDisputeModalOpen] = useState(false);
  const [disputeReason, setDisputeReason] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const pickupQuery = useCitizenPickupDetail(requestId);
  const cancelPickupMutation = useCancelCitizenPickup();
  const confirmWeightMutation = useConfirmPickupWeight();
  const disputeWeightMutation = useDisputePickupWeight();

  const request = pickupQuery.data;
  const isEligibleForContact =
    request &&
    request.assignment !== null &&
    ["accepted", "on_the_way", "collected", "weight_recorded", "disputed"].includes(request.status);
  const isVerificationOpen = request?.status === "weight_recorded";
  const isDisputed = request?.status === "disputed";
  const isCompleted = request?.status === "completed";

  return (
    <>
      <SeoHead
        title="Pickup Details"
        description="View the full Waste-IQ pickup timeline, collector assignment, and citizen request details."
        path={`/dashboard/pickups/${requestId}`}
      />

      <PageHeader
        title={`Pickup Request #${requestId}`}
        description="Track your pickup status, view collector details, and verify the recorded weight."
        actions={
          <Button asChild variant="outline">
            <Link to="/dashboard/pickups">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Pickups
            </Link>
          </Button>
        }
      />

      {pickupQuery.isPending && !request ? (
        <LoadingSkeleton variant="detail" />
      ) : pickupQuery.isError ? (
        <ErrorState
          error={pickupQuery.error}
          fallback="Unable to load this pickup request. Please try again."
          onRetry={() => pickupQuery.refetch()}
          isRetrying={pickupQuery.isFetching}
          title="Unable to load pickup details"
        />
      ) : request ? (
        <div className="space-y-6">
          <DashboardCard
            title={request.waste_type}
            description={`Submitted on ${formatDateTime(request.created_at)}`}
            actions={
              <div className="flex flex-wrap items-center gap-2">
                {isEligibleForContact ? (
                  <Button variant="outline" onClick={() => setIsContactModalOpen(true)}>
                    <PhoneCall className="mr-2 h-4 w-4" />
                    Contact Collector
                  </Button>
                ) : null}
                {request.can_cancel ? (
                  <Button variant="destructive" onClick={() => setIsCancelDialogOpen(true)}>
                    Cancel Request
                  </Button>
                ) : null}
              </div>
            }
          >
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge status={request.status} />
                <p className="text-sm text-muted-foreground">
                  Request ID: #{request.id}
                </p>
              </div>
              <ProgressTracker currentStatus={request.status} />
            </div>
          </DashboardCard>

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="space-y-6">
              <DashboardCard title="Pickup Details" description="Backend-provided request metadata.">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      Requested Date
                    </p>
                    <p className="mt-2 font-medium">{formatDateTime(request.created_at)}</p>
                  </div>
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      Scheduled Date
                    </p>
                    <p className="mt-2 font-medium">
                      {request.preferred_time
                        ? formatDateTime(request.preferred_time)
                        : "No preferred time set"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      Waste Type
                    </p>
                    <p className="mt-2 font-medium">{request.waste_type}</p>
                  </div>
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      Estimated Weight
                    </p>
                    <p className="mt-2 font-medium">{formatWeight(request.estimated_weight_kg)}</p>
                  </div>
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      AI Category
                    </p>
                    <p className="mt-2 font-medium">
                      {request.category && request.category !== "Unknown"
                        ? `${request.category}${
                            request.confidence != null
                              ? ` (${(request.confidence * 100).toFixed(0)}% confidence)`
                              : ""
                          }`
                        : request.category ?? "No AI category returned"}
                    </p>
                    {request.category && request.category === "Unknown" ? (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Classification preview on standby until the AI model is live.
                      </p>
                    ) : null}
                  </div>
                  {request.notes ? (
                    <div className="rounded-2xl bg-muted/20 p-4 sm:col-span-2">
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                        Notes
                      </p>
                      <p className="mt-2 text-sm text-muted-foreground">{request.notes}</p>
                    </div>
                  ) : null}
                </div>
              </DashboardCard>

              <DashboardCard title="Address and Coordinates" description="Citizen-provided pickup location.">
                <div className="space-y-4">
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <div className="flex items-center gap-2 font-medium">
                      <MapPinned className="h-4 w-4 text-primary" />
                      Pickup Address
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{request.address}</p>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl bg-muted/20 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                        Latitude
                      </p>
                      <p className="mt-2 font-medium">{request.latitude}</p>
                    </div>
                    <div className="rounded-2xl bg-muted/20 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                        Longitude
                      </p>
                      <p className="mt-2 font-medium">{request.longitude}</p>
                    </div>
                  </div>
                </div>
              </DashboardCard>

              <DashboardCard title="Collector and Delivery Flow" description="Assignment details returned by the backend.">
                <div className="space-y-4">
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-medium">
                        <Truck className="h-4 w-4 text-primary" />
                        Collector
                      </div>
                      {isEligibleForContact ? (
                        <Button size="sm" variant="ghost" className="text-primary text-xs" onClick={() => setIsContactModalOpen(true)}>
                          <PhoneCall className="mr-1.5 h-3.5 w-3.5" />
                          Contact Collector
                        </Button>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {request.assigned_collector_name ?? "No collector assigned yet."}
                    </p>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-2xl bg-muted/20 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                        Accepted At
                      </p>
                      <p className="mt-2 font-medium">
                        {request.assignment
                          ? formatDateTime(request.assignment.accepted_at)
                          : "Not accepted yet"}
                      </p>
                    </div>
                    <div className="rounded-2xl bg-muted/20 p-4">
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                        ETA
                      </p>
                      <p className="mt-2 font-medium">Not provided by the current API</p>
                    </div>
                    <div className="rounded-2xl bg-muted/20 p-4 sm:col-span-2">
                      <div className="flex items-center gap-2 font-medium">
                        <Clock3 className="h-4 w-4 text-primary" />
                        Final Reported Weight
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">
                        {formatWeight(request.assignment?.weight_kg)}
                      </p>
                    </div>
                  </div>
                </div>
              </DashboardCard>

              {(isVerificationOpen || isDisputed || isCompleted) && request.assignment?.weight_kg != null ? (
                <DashboardCard
                  title="Weight Verification"
                  description="Review the collector-recorded weight and confirm or dispute it."
                >
                  <div className="space-y-4">
                    {request.estimated_weight_kg != null ? (
                      <div className="grid gap-3 rounded-2xl border bg-muted/20 p-4 sm:grid-cols-2">
                        <div>
                          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                            Your Estimated Weight
                          </p>
                          <p className="mt-1 text-lg font-semibold">
                            {formatWeight(request.estimated_weight_kg)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                            Collector Recorded
                          </p>
                          <p className="mt-1 text-lg font-semibold text-primary">
                            {formatWeight(request.assignment.weight_kg)}
                          </p>
                        </div>
                      </div>
                    ) : null}

                    <div className="flex items-center justify-between rounded-2xl bg-muted/20 p-4">
                      <div>
                        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                          Recorded Weight
                        </p>
                        <p className="mt-1 text-2xl font-bold">
                          {formatWeight(request.assignment.weight_kg)}
                        </p>
                      </div>
                      <StatusBadge status={request.status} />
                    </div>

                    {isVerificationOpen ? (
                      <div className="space-y-3">
                        <div className="rounded-2xl border border-primary/20 bg-primary/5 p-3 text-sm text-primary">
                          <div className="flex items-start gap-2">
                            <Info className="mt-0.5 h-4 w-4 flex-shrink-0" />
                            <div>
                              <p className="font-medium">Confirming accepts the recorded weight.</p>
                              <p className="mt-1 text-xs opacity-90">
                                Disputing does not change the weight — it sends the pickup to an
                                admin for review. You will be notified once a decision is made.
                              </p>
                            </div>
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Please confirm that the recorded weight is accurate, or file a dispute
                          if you believe the weight is incorrect.
                        </p>
                        <div className="flex flex-wrap gap-3">
                          <Button
                            onClick={() =>
                              void confirmWeightMutation.mutateAsync(requestId).then(() => {
                                setActionError(null);
                              }).catch((e) => {
                                setActionError(getApiErrorMessage(e, "Confirmation failed. Please try again."));
                              })
                            }
                            disabled={
                              confirmWeightMutation.isPending ||
                              disputeWeightMutation.isPending
                            }
                            aria-busy={confirmWeightMutation.isPending}
                          >
                            {confirmWeightMutation.isPending ? "Confirming..." : "Confirm Weight"}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => {
                              setActionError(null);
                              setDisputeReason("");
                              setIsDisputeModalOpen(true);
                            }}
                            disabled={
                              confirmWeightMutation.isPending ||
                              disputeWeightMutation.isPending
                            }
                          >
                            Dispute Weight
                          </Button>
                        </div>
                        {actionError ? (
                          <div
                            role="alert"
                            className="flex items-start gap-2 rounded-2xl border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
                          >
                            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                            <span>{actionError}</span>
                          </div>
                        ) : null}
                      </div>
                    ) : null}

                    {isDisputed && request.dispute ? (
                      <div className="space-y-3">
                        <div className="flex items-start gap-3 rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
                          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                          <div>
                            <p className="font-medium text-amber-700 dark:text-amber-300">
                              Weight Disputed
                            </p>
                            <p className="mt-1 text-sm text-muted-foreground">
                              {request.dispute.reason}
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              Filed on {formatDateTime(request.dispute.disputed_at)}
                            </p>
                          </div>
                        </div>
                        <div className="rounded-2xl border bg-muted/20 p-3 text-sm text-muted-foreground">
                          <div className="flex items-start gap-2">
                            <HelpCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                            <p>
                              Your dispute has been submitted and is being reviewed by an admin.
                              We will notify you once a resolution is available.
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : null}

                    {isCompleted && !isDisputed ? (
                      <div className="flex items-center gap-2 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                        <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                          Weight confirmed and pickup completed.
                        </p>
                      </div>
                    ) : null}
                  </div>
                </DashboardCard>
              ) : null}
            </div>

            <div className="space-y-6">
              <DashboardCard title="Uploaded Image" description="Photo attached to the original citizen request.">
                {request.image_url ? (
                  <img
                    src={request.image_url}
                    alt={request.waste_type}
                    className="h-[22rem] w-full rounded-3xl object-cover"
                  />
                ) : (
                  <EmptyState
                    title="No image uploaded"
                    description="This pickup was created without an image attachment."
                  />
                )}
              </DashboardCard>

              <DashboardCard title="Status Timeline" description="Every backend status change is recorded here.">
                <Timeline events={request.timeline} />
              </DashboardCard>
            </div>
          </div>
        </div>
      ) : (
        <EmptyState
          title="Pickup request not found"
          description="The request may not exist or you may not have access to it."
        />
      )}

      <ConfirmationDialog
        isOpen={isCancelDialogOpen}
        title="Cancel this pickup request?"
        description="Only pending pickups can be cancelled. Waste-IQ will immediately update the request status."
        confirmLabel="Cancel Pickup"
        isPending={cancelPickupMutation.isPending}
        onClose={() => setIsCancelDialogOpen(false)}
        onConfirm={async () => {
          await cancelPickupMutation.mutateAsync(requestId);
          setIsCancelDialogOpen(false);
        }}
      />

      <Modal
        isOpen={isDisputeModalOpen}
        onClose={() => {
          if (!disputeWeightMutation.isPending) {
            setIsDisputeModalOpen(false);
            setDisputeReason("");
          }
        }}
        title="Dispute the reported weight"
        description="Disputing does NOT change the recorded weight. Your pickup will be sent to an admin for review, and you will be notified once resolved."
        footer={
          <>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsDisputeModalOpen(false);
                setDisputeReason("");
              }}
              disabled={disputeWeightMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={
                disputeReason.trim().length < 5 || disputeWeightMutation.isPending
              }
              aria-busy={disputeWeightMutation.isPending}
              onClick={() => {
                setActionError(null);
                void disputeWeightMutation
                  .mutateAsync({
                    requestId,
                    payload: { reason: disputeReason.trim() },
                  })
                  .then(() => {
                    setIsDisputeModalOpen(false);
                    setDisputeReason("");
                  })
                  .catch((e) => {
                    setActionError(getApiErrorMessage(e, "Dispute submission failed. Please try again."));
                  });
              }}
            >
              {disputeWeightMutation.isPending ? "Submitting..." : "Submit Dispute"}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
            <div className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <p>
                Provide a clear reason why you believe the recorded weight is incorrect. An admin
                will review your case.
              </p>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="dispute-reason">
              Reason <span className="text-destructive">*</span>
            </Label>
            <Input
              id="dispute-reason"
              value={disputeReason}
              onChange={(event) => setDisputeReason(event.target.value)}
              placeholder="e.g., The amount seems too high — I had about 5 kg of cardboard."
              minLength={5}
              maxLength={2000}
              aria-invalid={disputeReason.length > 0 && disputeReason.trim().length < 5}
              aria-describedby="dispute-reason-help dispute-reason-error"
              disabled={disputeWeightMutation.isPending}
            />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span id="dispute-reason-help">Minimum 5 characters required.</span>
              <span>{disputeReason.length} / 2000</span>
            </div>
            {disputeReason && disputeReason.trim().length < 5 ? (
              <p id="dispute-reason-error" className="text-sm text-destructive">
                Provide at least 5 characters describing the dispute.
              </p>
            ) : null}
            {actionError ? (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-xl border border-destructive/30 bg-destructive/10 p-2 text-sm text-destructive"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                <span>{actionError}</span>
              </div>
            ) : null}
          </div>
        </div>
      </Modal>

      <MaskedContactModal
        isOpen={isContactModalOpen}
        onClose={() => setIsContactModalOpen(false)}
        requestId={requestId}
        targetRole="collector"
      />
    </>
  );
}
