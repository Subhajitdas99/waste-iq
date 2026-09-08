import { useState } from "react";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/ui/button";
import type { WeightDisputeResolveRequest } from "@/types/pickup";
import { formatWeight } from "@/lib/pickup";

interface WeightDisputeDialogProps {
  isOpen: boolean;
  mode: "upheld" | "corrected";
  requestId: number;
  disputeReason: string;
  collectorWeightKg: number | null;
  collectorName: string | null;
  isPending?: boolean;
  apiError?: string | null;
  onConfirm: (payload: WeightDisputeResolveRequest) => void;
  onClose: () => void;
}

export function WeightDisputeDialog({
  isOpen,
  mode,
  requestId,
  disputeReason,
  collectorWeightKg,
  collectorName,
  isPending = false,
  apiError = null,
  onConfirm,
  onClose,
}: WeightDisputeDialogProps) {
  const [notes, setNotes] = useState("");
  const [correctedWeight, setCorrectedWeight] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleClose = () => {
    if (!isPending) {
      setNotes("");
      setCorrectedWeight("");
      setValidationError(null);
      onClose();
    }
  };

  const handleConfirm = () => {
    if (mode === "corrected") {
      const parsed = Number(correctedWeight);
      if (!correctedWeight.trim() || !Number.isFinite(parsed)) {
        setValidationError("Corrected weight is required and must be numeric.");
        return;
      }
      if (parsed < 0 || parsed > 10000) {
        setValidationError("Corrected weight must be between 0 and 10,000 kg.");
        return;
      }
      setValidationError(null);
      onConfirm({
        resolution: "corrected",
        resolved_weight_kg: parsed,
        notes: notes || null,
      });
    } else {
      onConfirm({
        resolution: "upheld",
        resolved_weight_kg: null,
        notes: notes || null,
      });
    }
  };

  const isCorrected = mode === "corrected";
  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={isCorrected ? "Correct pickup weight" : "Uphold collector weight"}
      description={
        isCorrected
          ? `Pickup #${requestId} — the original collector measurement will remain on record.`
          : `Pickup #${requestId} — the original collector measurement will be accepted.`
      }
      footer={
        <>
          <Button type="button" variant="outline" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            type="button"
            variant={isCorrected ? "default" : "default"}
            onClick={handleConfirm}
            disabled={isPending}
            aria-busy={isPending}
          >
            {isPending ? "Working..." : isCorrected ? "Correct Weight" : "Uphold Weight"}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="rounded-2xl border bg-muted/20 p-4">
          <p className="text-sm font-medium text-foreground">Pickup #{requestId}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Collector-reported weight: {collectorWeightKg === null ? "Not available" : formatWeight(collectorWeightKg)}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Citizen dispute reason: {disputeReason}
          </p>
          {collectorName ? (
            <p className="mt-1 text-sm text-muted-foreground">
              Collector: {collectorName}
            </p>
          ) : null}
        </div>

        {isCorrected ? (
          <div className="flex flex-col gap-2">
            <label htmlFor="corrected-weight" className="text-sm font-medium">
              Corrected weight (kg)
            </label>
            <input
              id="corrected-weight"
              type="number"
              min="0"
              max="10000"
              step="0.1"
              value={correctedWeight}
              onChange={(e) => {
                setCorrectedWeight(e.target.value);
                setValidationError(null);
              }}
              placeholder="Enter corrected weight"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={isPending}
            />
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            The original collector measurement will be accepted as final. No weight
            change is applied.
          </p>
        )}

        <div className="flex flex-col gap-2">
          <label htmlFor="dispute-notes" className="text-sm font-medium">
            Admin notes
          </label>
          <textarea
            id="dispute-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            maxLength={2000}
            placeholder="Optional notes for this resolution"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            disabled={isPending}
          />
        </div>

        {validationError || apiError ? (
          <div
            role="alert"
            className="rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            {validationError ?? apiError}
          </div>
        ) : null}
      </div>
    </Modal>
  );
}
