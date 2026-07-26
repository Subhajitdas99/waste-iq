import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Clock3, MapPinned, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SeoHead } from "@/components/seo/SeoHead";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { ProgressTracker } from "@/components/dashboard/ProgressTracker";
import { Timeline } from "@/components/dashboard/Timeline";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { LoadingSkeleton } from "@/components/dashboard/LoadingSkeleton";
import { ConfirmationDialog } from "@/components/dashboard/ConfirmationDialog";
import {
  useCancelCitizenPickup,
  useCitizenPickupDetail,
} from "@/hooks/useCitizenPickups";
import { getApiErrorMessage } from "@/lib/api-error";
import { formatDateTime, formatWeight } from "@/lib/pickup";

export function PickupDetailsPage() {
  const params = useParams();
  const requestId = Number(params.id ?? 0);
  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
  const pickupQuery = useCitizenPickupDetail(requestId);
  const cancelPickupMutation = useCancelCitizenPickup();

  const request = pickupQuery.data;

  return (
    <>
      <SeoHead
        title="Pickup Details"
        description="View the full Waste-IQ pickup timeline, collector assignment, and citizen request details."
        path={`/dashboard/pickups/${requestId}`}
      />

      <PageHeader
        title={`Pickup Request #${requestId}`}
        description="Track status transitions, collector assignment, and all backend-provided pickup metadata."
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
        <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {getApiErrorMessage(pickupQuery.error, "Unable to load this pickup request.")}
        </div>
      ) : request ? (
        <div className="space-y-6">
          <DashboardCard
            title={request.waste_type}
            description={`Submitted on ${formatDateTime(request.created_at)}`}
            actions={
              request.can_cancel ? (
                <Button variant="destructive" onClick={() => setIsCancelDialogOpen(true)}>
                  Cancel Request
                </Button>
              ) : null
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
                    <p className="mt-2 font-medium">Not provided by the current API</p>
                  </div>
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      Waste Type
                    </p>
                    <p className="mt-2 font-medium">{request.waste_type}</p>
                  </div>
                  <div className="rounded-2xl bg-muted/20 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                      AI Category
                    </p>
                    <p className="mt-2 font-medium">
                      {request.category ?? "No AI category returned"}
                    </p>
                  </div>
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
                    <div className="flex items-center gap-2 font-medium">
                      <Truck className="h-4 w-4 text-primary" />
                      Collector
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
    </>
  );
}
