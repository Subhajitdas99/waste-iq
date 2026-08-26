import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { CheckCircle2, Eye, EyeOff, Leaf, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { Spinner } from "@/components/ui/spinner";
import { SeoHead } from "@/components/seo/SeoHead";
import { resetPassword } from "@/api/auth";
import {
  getApiErrorMessage,
  getRateLimitRetryAfterSeconds,
  isRateLimitError,
} from "@/lib/api-error";

const resetPasswordSchema = z
  .object({
    newPassword: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type ResetPasswordValues = z.infer<typeof resetPasswordSchema>;

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordValues>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordValues) => {
    setApiError(null);
    if (!token) {
      setApiError("This reset link is invalid. Request a new one below.");
      return;
    }
    try {
      await resetPassword({ token, newPassword: data.newPassword });
      setSuccess(true);
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
      setApiError(getApiErrorMessage(error, "Unable to reset your password."));
    }
  };

  const passwordField = (show: boolean) => (show ? "text" : "password");

  return (
    <div className="w-full">
      <SeoHead
        title="Reset Password"
        description="Choose a new password for your Waste-IQ account."
        path="/reset-password"
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
        <h1 className="text-2xl font-bold tracking-tight">
          {success ? "Password reset" : "Set a new password"}
        </h1>
        <p className="text-sm text-muted-foreground mt-2">
          {success
            ? "Your password has been updated. Sign in with your new password."
            : "Choose a strong password for your account"}
        </p>
      </div>

      {!token ? (
        <div className="space-y-6">
          <div
            role="alert"
            className="flex items-start gap-3 p-4 bg-destructive/15 border border-destructive text-destructive text-sm rounded-md"
          >
            <XCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
            <p>This password reset link is missing its token.</p>
          </div>
          <Button asChild variant="outline" className="w-full h-11">
            <Link to="/forgot-password">Request a new reset link</Link>
          </Button>
        </div>
      ) : success ? (
        <div
          role="status"
          className="flex flex-col items-center gap-4 p-4 bg-primary/10 border border-primary/30 text-primary text-center rounded-md"
        >
          <CheckCircle2 className="h-8 w-8" aria-hidden="true" />
          <p className="text-sm">Your password has been reset successfully.</p>
          <Button asChild className="w-full h-11">
            <Link to="/login">Sign in</Link>
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          {apiError && (
            <div
              role="alert"
              data-testid="reset-api-error"
              className="flex items-start gap-3 p-4 bg-destructive/15 border border-destructive text-destructive text-sm rounded-md"
            >
              <XCircle className="h-5 w-5 shrink-0 mt-0.5" aria-hidden="true" />
              <p>{apiError}</p>
            </div>
          )}

          <div className="relative">
            <FormField
              label="New password"
              type={passwordField(showPassword)}
              autoComplete="new-password"
              placeholder="********"
              registration={register("newPassword")}
              error={errors.newPassword}
            />
            <button
              type="button"
              className="absolute right-3 top-[34px] text-muted-foreground hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring rounded"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide passwords" : "Show passwords"}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <FormField
            label="Confirm new password"
            type={passwordField(showPassword)}
            autoComplete="new-password"
            placeholder="********"
            registration={register("confirmPassword")}
            error={errors.confirmPassword}
          />

          <Button
            type="submit"
            className="w-full h-11 text-base"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <Spinner size={18} /> Resetting...
              </span>
            ) : (
              "Reset password"
            )}
          </Button>

          <div className="text-center pt-2">
            <Link
              to="/login"
              className="text-sm font-medium text-primary hover:underline"
            >
              Back to sign in
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}
