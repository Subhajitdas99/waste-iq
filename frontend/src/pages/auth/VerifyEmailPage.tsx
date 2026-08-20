import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Leaf, Mail, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { SeoHead } from "@/components/seo/SeoHead";
import { Spinner } from "@/components/ui/spinner";
import { resendVerification, verifyEmail } from "@/api/auth";
import { useAuth } from "@/context/AuthContext";
import { authQueryKeys } from "@/hooks/auth-query-keys";
import { getApiErrorMessage, getRateLimitRetryAfterSeconds, isRateLimitError } from "@/lib/api-error";

type VerifyState = "verifying" | "success" | "already-verified" | "error";

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const { user, isAuthenticated } = useAuth();
  const token = searchParams.get("token");
  const [state, setState] = useState<VerifyState>(() => (token ? "verifying" : "error"));
  const [message, setMessage] = useState<string | null>(null);
  const [resendEmail, setResendEmail] = useState(user?.email ?? "");
  const [resendMessage, setResendMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setState("error");
      return;
    }

    let isActive = true;
    setState("verifying");
    setMessage(null);

    verifyEmail(token)
      .then((response) => {
        if (!isActive) {
          return;
        }
        setState(response.message === "Email already verified" ? "already-verified" : "success");
        setMessage(response.message);
        // The cached profile still reports the stale verification state;
        // refetch so the dashboard banner disappears immediately.
        queryClient.invalidateQueries({ queryKey: authQueryKeys.currentUser });
      })
      .catch(() => {
        if (!isActive) {
          return;
        }
        setState("error");
      });

    return () => {
      isActive = false;
    };
  }, [token, queryClient]);

  const resendMutation = useMutation({
    meta: {
      suppressGlobalError: true,
    },
    mutationFn: resendVerification,
    onSuccess: (response) => {
      setResendMessage(response.message);
    },
  });

  const onResend = async (event: React.FormEvent) => {
    event.preventDefault();
    setResendMessage(null);
    try {
      await resendMutation.mutateAsync(resendEmail);
    } catch (error) {
      if (isRateLimitError(error)) {
        const seconds = getRateLimitRetryAfterSeconds(error);
        const minutes = seconds !== null ? Math.max(1, Math.ceil(seconds / 60)) : null;
        setResendMessage(
          minutes !== null
            ? `Too many attempts. Please try again in about ${minutes} minute${minutes === 1 ? "" : "s"}.`
            : "Too many attempts. Please try again later."
        );
        return;
      }
      setResendMessage(getApiErrorMessage(error, "Unable to resend the verification email."));
    }
  };

  const heading =
    state === "verifying"
      ? "Verifying your email"
      : state === "success"
        ? "Email verified"
        : state === "already-verified"
          ? "Email already verified"
          : "Verify your email";

  return (
    <div className="w-full">
      <SeoHead
        title="Verify Email"
        description="Verify your Waste-IQ email address to secure your account."
        path="/verify-email"
      />

      <div className="text-center mb-8">
        <Link
          to="/"
          className="inline-flex items-center gap-2 mb-6 text-primary hover:opacity-80 transition-opacity"
        >
          <Leaf className="h-6 w-6" aria-hidden="true" />
          <span className="font-bold text-xl tracking-tight text-foreground">
            Waste-IQ
          </span>
        </Link>
        <h1 className="text-2xl font-bold tracking-tight">{heading}</h1>
        <p className="text-sm text-muted-foreground mt-2">
          {state === "verifying"
            ? "Please wait while we confirm your verification link..."
            : "Confirm your account to unlock the full Waste-IQ experience."}
        </p>
      </div>

      {state === "verifying" && (
        <div role="status" className="flex justify-center py-6">
          <Spinner size={28} />
        </div>
      )}

      {state === "success" && (
        <div
          role="status"
          className="flex flex-col items-center gap-4 p-4 bg-primary/10 border border-primary/30 text-primary text-center rounded-md"
        >
          <CheckCircle2 className="h-8 w-8" aria-hidden="true" />
          <p className="text-sm">{message ?? "Email verified successfully"}</p>
          <Button asChild className="w-full h-11">
            <Link to={isAuthenticated ? "/dashboard/overview" : "/login"}>
              {isAuthenticated ? "Go to dashboard" : "Sign in"}
            </Link>
          </Button>
        </div>
      )}

      {state === "already-verified" && (
        <div
          role="status"
          className="flex flex-col items-center gap-4 p-4 bg-primary/10 border border-primary/30 text-primary text-center rounded-md"
        >
          <CheckCircle2 className="h-8 w-8" aria-hidden="true" />
          <p className="text-sm">{message ?? "Email already verified"}</p>
          <Button asChild className="w-full h-11">
            <Link to={isAuthenticated ? "/dashboard/overview" : "/login"}>
              {isAuthenticated ? "Go to dashboard" : "Sign in"}
            </Link>
          </Button>
        </div>
      )}

      {state === "error" && (
        <div className="space-y-6">
          {token && (
            <div
              role="alert"
              className="flex items-start gap-3 p-4 bg-destructive/15 border border-destructive text-destructive text-sm rounded-md"
            >
              <XCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
              <p>
                This verification link is invalid or expired. You can request a new
                verification email below.
              </p>
            </div>
          )}

          <form onSubmit={onResend} className="space-y-4" noValidate>
            <FormField
              id="resend-email"
              label="Email address"
              type="email"
              autoComplete="email"
              placeholder="name@example.com"
              registration={{}}
              value={resendEmail}
              onChange={(event) => setResendEmail(event.target.value)}
            />

            <Button
              type="submit"
              className="w-full h-11 text-base gap-2"
              disabled={resendMutation.isPending}
            >
              {resendMutation.isPending ? (
                <span className="flex items-center gap-2">
                  <Spinner size={18} /> Sending...
                </span>
              ) : (
                <>
                  <Mail className="h-4 w-4" aria-hidden="true" />
                  Resend verification email
                </>
              )}
            </Button>
          </form>

          {resendMessage && (
            <div
              role={resendMutation.isError ? "alert" : "status"}
              className={`p-3 border text-sm rounded-md ${
                resendMutation.isError
                  ? "bg-destructive/15 border-destructive text-destructive"
                  : "bg-primary/15 border-primary/30 text-primary"
              }`}
            >
              {resendMessage}
            </div>
          )}
        </div>
      )}

      <div className="text-center mt-6">
        <p className="text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}