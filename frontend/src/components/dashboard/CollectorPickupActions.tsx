import { useState } from "react";
import { AlertCircle, Scale, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Modal } from "@/components/Modal";
import { ConfirmationDialog } from "@/components/dashboard/ConfirmationDialog";
import {
  useAcceptCollectorPickup,
  useCancelCollectorPickup,
  useCollectCollectorPickup,
  useCompleteCollectorPickup,
  useRecordWeightCollectorPickup,
  useStartCollectorPickup,
} from "@/hooks/useCollectorRequests";
import { getApiErrorMessage } from "@/lib/api-error";
import { formatWeight } from "@/lib/pickup";
import type { PickupRequest } from "@/types/pickup";

interface CollectorPickupActionsProps {
  request: PickupRequest;
}

export function CollectorPickupActions({ request }: CollectorPickupActionsProps) {
  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
  const [isWeightDialogOpen, setIsWeightDialogOpen] = useState(false);
  const [weightInput, setWeightInput] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const acceptMutation = useAcceptCollectorPickup();
  const startMutation = useStartCollectorPickup();
  const collectMutation = useCollectCollectorPickup();
  const recordWeightMutation = useRecordWeightCollectorPickup();
  const completeMutation = useCompleteCollectorPickup();
  const cancelMutation = useCancelCollectorPickup();

  const isWorking =
    acceptMutation.isPending ||
    startMutation.isPending ||
    collectMutation.isPending ||
    recordWeightMutation.isPending ||
    completeMutation.isPending ||
    cancelMutation.isPending;

  const run = async (action: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await action();
    } catch (error) {
      setActionError(
        getApiErrorMessage(
          error,
          "The action failed. Please check the request state and retry.",
        ),
      );
    }
  };

  if (request.status === "completed" || request.status === "cancelled") {
    return null;
  }

  const numericWeight = Number(weightInput);
  const isWeightValid = Number.isFinite(numericWeight) && numericWeight > 0;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3">
        {request.status === "pending" ? (
          <Button
            type="button"
            disabled={isWorking}
            aria-busy={acceptMutation.isPending}
            onClick={() => void run(() => acceptMutation.mutateAsync(request.id))}
          >
            {acceptMutation.isPending ? "Accepting..." : "Accept Request"}
          </Button>
        ) : null}

        {request.status === "accepted" ? (
          <>
            <Button
              type="button"
              disabled={isWorking}
              aria-busy={startMutation.isPending}
              onClick={() => void run(() => startMutation.mutateAsync(request.id))}
            >
              {startMutation.isPending ? "Starting..." : "Start Trip"}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={isWorking}
              onClick={() => {
                setActionError(null);
                setIsCancelDialogOpen(true);
              }}
            >
              Release Request
            </Button>
          </>
        ) : null}

        {request.status === "on_the_way" ? (
          <Button
            type="button"
            disabled={isWorking}
            aria-busy={collectMutation.isPending}
            onClick={() => void run(() => collectMutation.mutateAsync(request.id))}
          >
            {collectMutation.isPending ? "Confirming..." : "Mark as Collected"}
          </Button>
        ) : null}

        {request.status === "collected" ? (
          <Button
            type="button"
            disabled={isWorking}
            onClick={() => {
              setActionError(null);
              setWeightInput(
                request.estimated_weight_kg != null
                  ? String(request.estimated_weight_kg)
                  : "",
              );
              setIsWeightDialogOpen(true);
            }}
          >
            <Scale className="mr-2 h-4 w-4" />
            Record Weight
          </Button>
        ) : null}

        {request.status === "weight_recorded" ? (
          <div
            className="flex flex-col gap-2"
            role="status"
            aria-live="polite"
          >
            <span className="rounded-2xl border border-indigo-500/20 bg-indigo-500/10 px-4 py-2 text-sm font-medium text-indigo-700 dark:text-indigo-300">
              Weight recorded — awaiting citizen confirmation
            </span>
            <p className="text-xs text-muted-foreground">
              Once the citizen confirms the weight, this pickup will be marked as completed.
            </p>
          </div>
        ) : null}

        {request.status === "disputed" ? (
          <div className="flex flex-col gap-2" role="status" aria-live="polite">
            <span className="rounded-2xl border border-amber-500/20 bg-amber-500/10 px-4 py-2 text-sm font-medium text-amber-700 dark:text-amber-300">
              Weight disputed — under admin review
            </span>
            <p className="text-xs text-muted-foreground">
              The citizen has disputed the recorded weight. An admin will review and resolve.
            </p>
          </div>
        ) : null}
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

      <ConfirmationDialog
        isOpen={isCancelDialogOpen}
        title="Release this pickup request?"
        description="The request will return to the available queue so another collector can accept it. This is only possible before the trip starts."
        confirmLabel="Yes, Release"
        cancelLabel="Keep Request"
        isPending={cancelMutation.isPending}
        onClose={() => setIsCancelDialogOpen(false)}
        onConfirm={async () => {
          setActionError(null);
          try {
            await cancelMutation.mutateAsync(request.id);
            setIsCancelDialogOpen(false);
          } catch (error) {
            setActionError(
              getApiErrorMessage(
                error,
                "Unable to release the request. It may no longer be cancellable.",
              ),
            );
          }
        }}
      />

      <Modal
        isOpen={isWeightDialogOpen}
        onClose={() => {
          if (!recordWeightMutation.isPending) {
            setIsWeightDialogOpen(false);
            setWeightInput("");
            setActionError(null);
          }
        }}
        title="Record weight"
        description="Record the measured weight of the collected waste. The pickup will then wait for citizen confirmation."
        footer={
          <>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsWeightDialogOpen(false);
                setWeightInput("");
                setActionError(null);
              }}
              disabled={recordWeightMutation.isPending}
            >
              <X className="mr-1 h-4 w-4" />
              Cancel
            </Button>
            <Button
              type="button"
              disabled={!isWeightValid || recordWeightMutation.isPending}
              aria-busy={recordWeightMutation.isPending}
              onClick={() => {
                setActionError(null);
                void run(async () => {
                  await recordWeightMutation.mutateAsync({
                    requestId: request.id,
                    weightKg: numericWeight,
                  });
                  setIsWeightDialogOpen(false);
                  setWeightInput("");
                });
              }}
            >
              {recordWeightMutation.isPending ? "Recording..." : "Confirm Weight"}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          {request.estimated_weight_kg != null ? (
            <div className="rounded-xl border bg-muted/20 p-3 text-sm text-muted-foreground">
              <p>
                Citizen-estimated weight:{" "}
                <span className="font-medium text-foreground">
                  {formatWeight(request.estimated_weight_kg)}
                </span>
              </p>
            </div>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="weight">Final weight (kg)</Label>
            <Input
              id="weight"
              type="number"
              min="0"
              step="0.1"
              inputMode="decimal"
              value={weightInput}
              onChange={(event) => setWeightInput(event.target.value)}
              placeholder="e.g. 12.5"
              aria-invalid={weightInput.length > 0 && !isWeightValid}
              aria-describedby="weight-help weight-error"
              disabled={recordWeightMutation.isPending}
              autoFocus
            />
            <p id="weight-help" className="text-xs text-muted-foreground">
              Enter the actual measured weight in kilograms (e.g., 12.5).
            </p>
            {weightInput && !isWeightValid ? (
              <p id="weight-error" className="text-sm text-destructive">
                Enter a weight greater than zero.
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
    </div>
  );
}
