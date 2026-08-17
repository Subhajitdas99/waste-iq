import { useState } from "react";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/ui/button";

interface DealerApprovalDialogProps {
  isOpen: boolean;
  mode: "approve" | "reject";
  dealerName: string;
  isPending: boolean;
  onConfirm: (reason?: string) => void;
  onClose: () => void;
}

export function DealerApprovalDialog({
  isOpen,
  mode,
  dealerName,
  isPending,
  onConfirm,
  onClose,
}: DealerApprovalDialogProps) {
  const [reason, setReason] = useState("");

  const isReject = mode === "reject";

  const handleConfirm = () => {
    if (isReject && reason.trim().length === 0) {
      return;
    }
    onConfirm(isReject ? reason.trim() : undefined);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isReject ? "Reject dealer application" : "Approve dealer application"}
      description={
        isReject
          ? `Reject ${dealerName}'s profile. A reason is required and will be shown to the dealer.`
          : `Approve ${dealerName}'s profile to grant marketplace access.`
      }
      footer={
        <>
          <Button type="button" variant="outline" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            type="button"
            variant={isReject ? "destructive" : "default"}
            onClick={handleConfirm}
            disabled={isPending || (isReject && reason.trim().length === 0)}
          >
            {isPending ? "Working..." : isReject ? "Reject" : "Approve"}
          </Button>
        </>
      }
    >
      {isReject ? (
        <label htmlFor="rejection-reason" className="flex flex-col gap-2">
          <span className="text-sm font-medium">Rejection reason</span>
          <textarea
            id="rejection-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            rows={4}
            maxLength={500}
            placeholder="Explain why the application was rejected"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </label>
      ) : (
        <p className="text-sm text-muted-foreground">
          This will mark the profile as approved and immediately unlock dealer
          inventory access for this account.
        </p>
      )}
    </Modal>
  );
}
