import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Eye, EyeOff, Leaf } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { Checkbox } from "@/components/ui/checkbox";
import { Spinner } from "@/components/ui/spinner";
import { SeoHead } from "@/components/seo/SeoHead";
import { useLogin } from "@/hooks/useLogin";
import { resolvePostLoginPath } from "@/lib/portal";
import { getApiErrorMessage, getRateLimitRetryAfterSeconds, isRateLimitError } from "@/lib/api-error";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
  rememberMe: z.boolean(),
});

type LoginValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const loginMutation = useLogin();

  const locationState = location.state as {
    from?: { pathname?: string };
    registered?: boolean;
    registeredEmail?: string;
  } | null;

  const from = locationState?.from?.pathname;
  const justRegistered = locationState?.registered === true;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: locationState?.registeredEmail ?? "",
      rememberMe: false,
    },
  });

  const rememberMe = watch("rememberMe");

  const onSubmit = async (data: LoginValues) => {
    setApiError(null);
    try {
      const response = await loginMutation.mutateAsync({
        email: data.email,
        password: data.password,
        rememberMe: data.rememberMe,
      });
      navigate(resolvePostLoginPath(response.user.role, from), { replace: true });
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
      setApiError(getApiErrorMessage(error, "Invalid email or password"));
    }
  };

  return (
    <div className="w-full">
      <SeoHead
        title="Sign In"
        description="Sign in to your Waste-IQ account to manage waste pickups and track recycling."
        path="/login"
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
        <h1 className="text-2xl font-bold tracking-tight">Welcome back</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Enter your credentials to access your account
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {justRegistered && (
          <div
            role="status"
            className="p-3 bg-primary/15 border border-primary/30 text-primary text-sm rounded-md"
          >
            Account created successfully. Please sign in.
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

        <FormField
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="name@example.com"
          registration={register("email")}
          error={errors.email}
        />

        <div className="relative">
          <FormField
            label="Password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
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

        <div className="flex items-center justify-between mt-2 mb-6">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="rememberMe"
              checked={rememberMe}
              onCheckedChange={(checked) =>
                setValue("rememberMe", checked === true)
              }
            />
            <label
              htmlFor="rememberMe"
              className="text-sm font-medium leading-none cursor-pointer"
            >
              Remember me
            </label>
          </div>
        </div>

        <Button
          type="submit"
          className="w-full h-11 text-base"
          disabled={isSubmitting || loginMutation.isPending}
        >
          {isSubmitting || loginMutation.isPending ? (
            <span className="flex items-center gap-2">
              <Spinner size={18} /> Signing in...
            </span>
          ) : (
            "Sign in"
          )}
        </Button>
      </form>

      <div className="text-center mt-6">
        <p className="text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link
            to="/register"
            className="font-medium text-primary hover:underline"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
