import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { CheckCircle2, Leaf, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { Spinner } from "@/components/ui/spinner";
import { SeoHead } from "@/components/seo/SeoHead";
import { forgotPassword } from "@/api/auth";
import {
  getApiErrorMessage,
  getRateLimitRetryAfterSeconds,
  isRateLimitError,
} from "@/lib/api-error";

const forgotPasswordSchema = z.object({
  email: z.string().trim().email("Please enter a valid email address"),
});

type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>;

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (_data: ForgotPasswordValues) => {
    setApiError(null);
    try {
      await forgotPassword({ email: _data.email.trim() });
      // The response is identical whether or not the account exists, so the
      // same confirmation is shown in every case.
      setSubmitted(true);
    } catch (error) {
      if (isRateLimitError(error)) {
        const seconds = getRateLimitRetryAfterSeconds(error);
        const minutes = seconds !== null ? Math.max(1, Math.ceil(seconds / 60)) : null;
        setApiError(
          minutes !== null
            ? `Too many attempts. Please try again in about ${minutes} minute${minutes === 1 ? "" : "s"}.`
            : "Too many attempts. Please try again later."
        );
        return;
      }
      setApiError(
        getApiErrorMessage(error, "Unable to send the reset link. Please try again.")
      );
    }
  };

  return (
    <div className="w-full">
      <SeoHead
        title="Forgot Password"
        description="Request a password reset link for your Waste-IQ account."
        path="/forgot-password"
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
        <h1 className="text-2xl font-bold tracking-tight">Forgot your password?</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Enter your email address and we will send you a reset link
        </p>
      </div>

      {submitted ? (
        <div
          role="status"
          className="flex flex-col items-center gap-4 p-4 bg-primary/10 border border-primary/30 text-primary text-center rounded-md"
        >
          <CheckCircle2 className="h-8 w-8" aria-hidden="true" />
          <p className="text-sm">
            If the email is registered, a password reset link has been sent.
            Please check your inbox.
          </p>
          <Button asChild variant="outline" className="w-full h-11">
            <Link to="/login">Back to sign in</Link>
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          {apiError && (
            <div
              role="alert"
              className="p-3 bg-destructive/15 border border-destructive text-destructive text-sm rounded-md"
            >
              {apiError}
            </div>
          )}

          <FormField
            label="Email address"
            type="email"
            autoComplete="email"
            placeholder="name@example.com"
            registration={register("email")}
            error={errors.email}
          />

          <Button
            type="submit"
            className="w-full h-11 text-base gap-2"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <Spinner size={18} /> Sending...
              </span>
            ) : (
              <>
                <Mail className="h-4 w-4" aria-hidden="true" />
                Send reset link
              </>
            )}
          </Button>
        </form>
      )}

      <div className="text-center mt-6">
        <p className="text-sm text-muted-foreground">
          Remembered it?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
