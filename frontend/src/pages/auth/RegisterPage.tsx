import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Eye, EyeOff, Leaf } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { Checkbox } from "@/components/ui/checkbox";
import { Spinner } from "@/components/ui/spinner";
import { SeoHead } from "@/components/seo/SeoHead";
import api from "@/api/axios";
import { getApiErrorMessage } from "@/lib/api-error";

const registerSchema = z
  .object({
    name: z.string().min(2, "Full name must be at least 2 characters"),
    email: z.string().email("Please enter a valid email address"),
    phone: z
      .string()
      .min(8, "Phone must be at least 8 characters")
      .max(20, "Phone must be at most 20 characters"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
    role: z.enum(["citizen", "collector", "dealer", "admin"]),
    admin_code: z.string().optional(),
    termsAccepted: z.boolean().refine((val) => val === true, {
      message: "You must accept the terms and conditions",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  })
  .refine(
    (data) => data.role !== "admin" || (data.admin_code && data.admin_code.length > 0),
    {
      message: "Admin registration code is required",
      path: ["admin_code"],
    }
  );

type RegisterValues = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: "citizen", termsAccepted: false },
  });

  const termsAccepted = watch("termsAccepted");
  const selectedRole = watch("role");

  const onSubmit = async (data: RegisterValues) => {
    setApiError(null);
    try {
      await api.post("/auth/register", {
        name: data.name,
        email: data.email,
        phone: data.phone,
        password: data.password,
        role: data.role,
        ...(data.role === "admin" && data.admin_code
          ? { admin_code: data.admin_code }
          : {}),
      });

      navigate("/login", { replace: true, state: { registered: true } });
    } catch (error) {
      setApiError(getApiErrorMessage(error, "Registration failed. Please try again."));
    }
  };

  return (
    <div className="w-full max-w-lg mx-auto">
      <SeoHead
        title="Create Account"
        description="Join Waste-IQ to schedule pickups, collect waste, or trade recyclables on our digital marketplace."
        path="/register"
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
        <h1 className="text-2xl font-bold tracking-tight">Create an account</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Join the Waste-IQ platform to start making a difference
        </p>
      </div>

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
          label="Full Name"
          type="text"
          autoComplete="name"
          placeholder="John Doe"
          registration={register("name")}
          error={errors.name}
        />

        <FormField
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="name@example.com"
          registration={register("email")}
          error={errors.email}
        />

        <FormField
          label="Phone"
          type="tel"
          autoComplete="tel"
          placeholder="+1 (555) 000-0000"
          registration={register("phone")}
          error={errors.phone}
        />

        <div className="flex flex-col space-y-2 mb-4">
          <label htmlFor="role" className="text-sm font-medium leading-none">
            Account Type
          </label>
          <select
            id="role"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            {...register("role")}
          >
            <option value="citizen">Citizen (Schedule Pickups)</option>
            <option value="collector">Collector (Perform Pickups)</option>
            <option value="dealer">Dealer (Buy Recyclables)</option>
            <option value="admin">Administrator</option>
          </select>
        </div>

        {selectedRole === "admin" && (
          <FormField
            label="Admin Registration Code"
            type="password"
            placeholder="Enter admin code"
            registration={register("admin_code")}
            error={errors.admin_code}
          />
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <FormField
              label="Password"
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

          <FormField
            label="Confirm Password"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            placeholder="********"
            registration={register("confirmPassword")}
            error={errors.confirmPassword}
          />
        </div>

        <div className="flex items-start space-x-2 mt-4 mb-6">
          <Checkbox
            id="terms"
            checked={termsAccepted}
            onCheckedChange={(checked) =>
              setValue("termsAccepted", checked === true)
            }
            className="mt-1"
          />
          <div className="grid gap-1.5 leading-none">
            <label
              htmlFor="terms"
              className={`text-sm font-medium leading-none cursor-pointer ${errors.termsAccepted ? "text-destructive" : ""}`}
            >
              Accept terms and conditions
            </label>
            <p className="text-sm text-muted-foreground">
              You agree to our Terms of Service and Privacy Policy.
            </p>
            {errors.termsAccepted && (
              <span className="text-sm font-medium text-destructive">
                {errors.termsAccepted.message}
              </span>
            )}
          </div>
        </div>

        <Button
          type="submit"
          className="w-full h-11 text-base"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <Spinner size={18} /> Creating account...
            </span>
          ) : (
            "Create account"
          )}
        </Button>
      </form>

      <div className="text-center mt-6">
        <p className="text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-medium text-primary hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
