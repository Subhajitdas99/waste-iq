import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Leaf, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { Spinner } from "@/components/ui/spinner";
import { SeoHead } from "@/components/seo/SeoHead";
import api from "@/api/client";
import { getApiErrorMessage } from "@/lib/api-error";

const resetPasswordSchema = z.object({
  password: z.string().min(8, "Password must be at least 8 characters").max(64, "Password must not exceed 64 characters"),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type ResetPasswordValues = z.infer<typeof resetPasswordSchema>;

export function ResetPasswordPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      setApiError("Invalid or missing password reset token. Please request a new link.");
    }
  }, [token]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordValues>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordValues) => {
    if (!token) return;
    
    setApiError(null);
    setSuccessMessage(null);
    try {
      const response = await api.post<{ message: string }>("/auth/reset-password", {
        token,
        new_password: data.password,
      });
      setSuccessMessage(response.data.message);
      
      // Redirect to login after 3 seconds
      setTimeout(() => navigate("/login"), 3000);
    } catch (error) {
      setApiError(getApiErrorMessage(error, "Invalid or expired token"));
    }
  };

  return (
    <div className="w-full">
      <SeoHead
        title="Reset Password"
        description="Create a new password for your Waste-IQ account."
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
        <h1 className="text-2xl font-bold tracking-tight">Create new password</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Your new password must be between 8 and 64 characters.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {successMessage && (
          <div
            role="status"
            className="p-3 bg-primary/15 border border-primary/30 text-primary text-sm rounded-md"
          >
            {successMessage}
            <div className="mt-2 text-xs">Redirecting to login...</div>
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

        {!successMessage && token && (
          <>
            <div className="relative">
              <FormField
                label="New Password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                placeholder="********"
                registration={register("password")}
                error={errors.password}
              />
              <button
                type="button"
                className="absolute right-3 top-[34px] text-muted-foreground hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring rounded"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <div className="relative">
              <FormField
                label="Confirm Password"
                type={showConfirmPassword ? "text" : "password"}
                autoComplete="new-password"
                placeholder="********"
                registration={register("confirmPassword")}
                error={errors.confirmPassword}
              />
              <button
                type="button"
                className="absolute right-3 top-[34px] text-muted-foreground hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring rounded"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                aria-label={showConfirmPassword ? "Hide password" : "Show password"}
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <Button
              type="submit"
              className="w-full h-11 text-base mt-6"
              disabled={isSubmitting || !token}
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <Spinner size={18} /> Resetting...
                </span>
              ) : (
                "Reset password"
              )}
            </Button>
          </>
        )}
      </form>
    </div>
  );
}
