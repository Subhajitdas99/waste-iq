import { useState } from "react";
import { Copy, Lock, PhoneCall, ShieldCheck, AlertCircle, Check } from "lucide-react";
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
  const [copied, setCopied] = useState(false);

  const handleClose = () => {
    setSession(null);
    setCopied(false);
    contactMutation.reset();
    onClose();
  };

  const handleInitiate = async () => {
    try {
      const data = await contactMutation.mutateAsync(requestId);
      setSession(data);
      setCopied(false);
    } catch {
      // Error is handled via contactMutation.error
    }
  };

  const handleRetry = () => {
    contactMutation.reset();
    void handleInitiate();
  };

  const handleCopy = async () => {
    if (!session?.masked_number) return;
    try {
      await navigator.clipboard.writeText(session.masked_number);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const targetLabel = targetRole === "citizen" ? "Citizen" : "Collector";
  const title = `Contact ${targetLabel}`;

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
                private. Personal phone numbers are never shared between participants.
              </p>
            </div>
          </div>
        </div>

        {contactMutation.isError ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-destructive" />
              <div className="flex-1">
                <p className="font-medium">Unable to establish contact</p>
                <p className="mt-1 text-xs">
                  {getApiErrorMessage(
                    contactMutation.error,
                    "The communication service is temporarily unavailable. Please try again in a moment.",
                  )}
                </p>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="mt-3"
                  onClick={handleRetry}
                  disabled={contactMutation.isPending}
                >
                  {contactMutation.isPending ? "Retrying..." : "Try again"}
                </Button>
              </div>
            </div>
          </div>
        ) : null}

        {session ? (
          <div className="space-y-4 rounded-xl border bg-muted/20 p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
                Masked Route Session
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
                Active
              </span>
            </div>

            {session.masked_number ? (
              <div className="rounded-lg bg-background p-3 border">
                <p className="text-xs text-muted-foreground">Privacy Proxy Phone Number</p>
                <div className="mt-1 flex items-center justify-between gap-2">
                  <p
                    className="text-lg font-bold tracking-wide font-mono text-primary"
                    aria-label="Masked phone number"
                  >
                    {session.masked_number}
                  </p>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={handleCopy}
                    aria-label={copied ? "Number copied" : "Copy phone number"}
                    className="h-8 px-2"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-600" />
                        <span className="ml-1 text-xs">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        <span className="ml-1 text-xs">Copy</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>
            ) : null}

            {session.instructions ? (
              <p className="text-sm text-muted-foreground">{session.instructions}</p>
            ) : null}

            {session.expires_at ? (
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <Lock className="h-3.5 w-3.5" />
                Session expires at{" "}
                {new Date(session.expires_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            ) : null}
          </div>
        ) : (
          <div className="text-center py-2 space-y-4">
            <p className="text-sm text-muted-foreground">
              Initiate a private masked contact session for Pickup Request #{requestId}. The other
              party will see only the proxy number.
            </p>
            <Button
              className="w-full sm:w-auto"
              disabled={contactMutation.isPending}
              onClick={handleInitiate}
              aria-busy={contactMutation.isPending}
            >
              <PhoneCall className="mr-2 h-4 w-4" />
              {contactMutation.isPending
                ? "Connecting..."
                : `Initiate Contact with ${targetLabel}`}
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}
