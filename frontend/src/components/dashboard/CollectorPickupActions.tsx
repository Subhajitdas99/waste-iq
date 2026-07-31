import { useState } from "react";
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
  useStartCollectorPickup,
} from "@/hooks/useCollectorRequests";
import { getApiErrorMessage } from "@/lib/api-error";
import type { PickupRequest } from "@/types/pickup";

interface CollectorPickupActionsProps {
  request: PickupRequest;
}

export function CollectorPickupActions({ request }: CollectorPickupActionsProps) {
  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
  const [isCompleteDialogOpen, setIsCompleteDialogOpen] = useState(false);
  const [weightInput, setWeightInput] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const acceptMutation = useAcceptCollectorPickup();
  const startMutation = useStartCollectorPickup();
  const collectMutation = useCollectCollectorPickup();
  const completeMutation = useCompleteCollectorPickup();
  const cancelMutation = useCancelCollectorPickup();

  const isWorking =
    acceptMutation.isPending ||
    startMutation.isPending ||
    collectMutation.isPending ||
    completeMutation.isPending ||
    cancelMutation.isPending;

  const run = async (action: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await action();
    } catch (error) {
      setActionError(
        getApiErrorMessage(error, "The action failed. Please check the request state and retry."),
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
              onClick={() => void run(() => startMutation.mutateAsync(request.id))}
            >
              {startMutation.isPending ? "Starting..." : "Start Trip"}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={isWorking}
              onClick={() => setIsCancelDialogOpen(true)}
            >
              Release Request
            </Button>
          </>
        ) : null}

        {request.status === "on_the_way" ? (
          <Button
            type="button"
            disabled={isWorking}
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
              setWeightInput("");
              setIsCompleteDialogOpen(true);
            }}
          >
            Complete Pickup
          </Button>
        ) : null}
      </div>

      {actionError ? (
        <p role="alert" className="text-sm text-destructive">
          {actionError}
        </p>
      ) : null}

      <ConfirmationDialog
        isOpen={isCancelDialogOpen}
        title="Release this pickup request?"
        description="The request will return to the available queue so another collector can accept it. This is only possible before the trip starts."
        confirmLabel="Yes, Release"
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
        isOpen={isCompleteDialogOpen}
        onClose={() => setIsCompleteDialogOpen(false)}
        title="Complete pickup"
        description="Record the final measured weight of the collected waste."
        footer={
          <>
            <Button
              type="button"
              variant="outline"
              disabled={completeMutation.isPending}
              onClick={() => setIsCompleteDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={!isWeightValid || completeMutation.isPending}
              onClick={() => {
                setActionError(null);
                void run(async () => {
                  await completeMutation.mutateAsync({
                    requestId: request.id,
                    weightKg: numericWeight,
                  });
                  setIsCompleteDialogOpen(false);
                });
              }}
            >
              {completeMutation.isPending ? "Completing..." : "Confirm Weight"}
            </Button>
          </>
        }
      >
        <div className="space-y-2">
          <Label htmlFor="final-weight">Final weight (kg)</Label>
          <Input
            id="final-weight"
            type="number"
            min="0"
            step="0.1"
            inputMode="decimal"
            value={weightInput}
            onChange={(event) => setWeightInput(event.target.value)}
            placeholder="e.g. 12.5"
          />
          {weightInput && !isWeightValid ? (
            <p className="text-sm text-destructive">Enter a weight greater than zero.</p>
          ) : null}
        </div>
      </Modal>
    </div>
  );
}
