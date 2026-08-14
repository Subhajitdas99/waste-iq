import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Leaf, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { Spinner } from "@/components/ui/spinner";
import { SeoHead } from "@/components/seo/SeoHead";
import api from "@/api/axios";
import { getApiErrorMessage } from "@/lib/api-error";

const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>;

export function ForgotPasswordPage() {
  const [apiError, setApiError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordValues) => {
    setApiError(null);
    setSuccessMessage(null);
    try {
      const response = await api.post<{ message: string }>("/auth/forgot-password", {
        email: data.email,
      });
      setSuccessMessage(response.data.message);
    } catch (error) {
      setApiError(getApiErrorMessage(error, "Something went wrong"));
    }
  };

  return (
    <div className="w-full">
      <SeoHead
        title="Forgot Password"
        description="Reset your Waste-IQ account password."
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
        <h1 className="text-2xl font-bold tracking-tight">Forgot password?</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Enter your email address and we'll send you a link to reset your password.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {successMessage && (
          <div
            role="status"
            className="p-3 bg-primary/15 border border-primary/30 text-primary text-sm rounded-md"
          >
            {successMessage}
          </div>
        )}

        {apiError && (
          <div
            role="alert"
            className="p-3 bg-destructive/15 border border-destructive text-destructive text-sm rounded-md"
          >
            {apiError}
          </div>
        )}

        {!successMessage && (
          <>
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
              className="w-full h-11 text-base mt-6"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <Spinner size={18} /> Sending...
                </span>
              ) : (
                "Send reset link"
              )}
            </Button>
          </>
        )}
      </form>

      <div className="text-center mt-6">
        <Link
          to="/login"
          className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
