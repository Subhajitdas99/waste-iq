import { useState } from "react";
import { Lock, PhoneCall, ShieldCheck, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/Modal";
import { useInitiateContact } from "@/hooks/useContact";
import { getApiErrorMessage } from "@/lib/api-error";
import type { ContactSessionRead } from "@/types/pickup";

interface MaskedContactModalProps {
  isOpen: boolean;
  onClose: () => void;
  requestId: number;
  targetRole: "citizen" | "collector";
}

export function MaskedContactModal({
  isOpen,
  onClose,
  requestId,
  targetRole,
}: MaskedContactModalProps) {
  const contactMutation = useInitiateContact();
  const [session, setSession] = useState<ContactSessionRead | null>(null);

  const handleClose = () => {
    setSession(null);
    contactMutation.reset();
    onClose();
  };

  const handleInitiate = async () => {
    try {
      const data = await contactMutation.mutateAsync(requestId);
      setSession(data);
    } catch {
      // Error is handled via contactMutation.error
    }
  };

  const title = targetRole === "citizen" ? "Contact Citizen" : "Contact Collector";

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={title}
      description="Route your communication privately through Waste-IQ without exposing personal phone numbers."
    >
      <div className="space-y-5">
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm text-primary">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
            <div>
              <p className="font-semibold">Privacy Guaranteed</p>
              <p className="mt-1 text-xs opacity-90">
                Contact is routed privately through Waste-IQ. Your real phone number will remain
                private.
              </p>
            </div>
          </div>
        </div>

        {contactMutation.isError ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-destructive" />
            <div>
              <p className="font-medium">Unable to establish contact</p>
              <p className="mt-1 text-xs">
                {getApiErrorMessage(
                  contactMutation.error,
                  "Communication service is currently unavailable.",
                )}
              </p>
            </div>
          </div>
        ) : null}

        {session ? (
          <div className="space-y-4 rounded-xl border bg-muted/20 p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                Masked Route Session
              </span>
              <span className="inline-flex items-center rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                Active
              </span>
            </div>

            {session.masked_number ? (
              <div className="rounded-lg bg-background p-3 text-center border">
                <p className="text-xs text-muted-foreground">Privacy Proxy Phone Number</p>
                <p className="mt-1 text-lg font-bold tracking-wide font-mono text-primary">
                  {session.masked_number}
                </p>
              </div>
            ) : null}

            <p className="text-sm text-muted-foreground">{session.instructions}</p>

            {session.expires_at ? (
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <Lock className="h-3.5 w-3.5" />
                Session expires at {new Date(session.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            ) : null}
          </div>
        ) : (
          <div className="text-center py-2 space-y-4">
            <p className="text-sm text-muted-foreground">
              Click below to initiate a private masked contact session for Pickup Request #{requestId}.
            </p>
            <Button
              className="w-full sm:w-auto"
              disabled={contactMutation.isPending}
              onClick={handleInitiate}
            >
              <PhoneCall className="mr-2 h-4 w-4" />
              {contactMutation.isPending ? "Connecting..." : `Initiate Contact with ${targetRole === "citizen" ? "Citizen" : "Collector"}`}
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}
