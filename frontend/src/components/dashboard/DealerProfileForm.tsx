import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/FormField";
import { Spinner } from "@/components/ui/spinner";
import { useCreateDealerProfile, useUpdateDealerProfile } from "@/hooks/useDealerProfile";
import { getApiErrorMessage } from "@/lib/api-error";
import type { DealerProfile, DealerProfilePayload } from "@/types/dealer";

const PHONE_PATTERN = /^\+?[0-9]{10,15}$/;

const profileSchema = z.object({
  business_name: z
    .string()
    .trim()
    .min(2, "Business name must be at least 2 characters")
    .max(160),
  owner_name: z
    .string()
    .trim()
    .min(2, "Owner name must be at least 2 characters")
    .max(120),
  phone: z
    .string()
    .trim()
    .regex(PHONE_PATTERN, "Enter a valid phone number (10-15 digits, optional leading +)"),
  email: z.union([
    z.literal(""),
    z.string().trim().email("Enter a valid email address").max(254),
  ]),
  address: z
    .string()
    .trim()
    .min(8, "Address must be at least 8 characters")
    .max(500),
  city: z.string().trim().min(2, "City must be at least 2 characters").max(100),
  state: z.string().trim().max(100),
  postal_code: z
    .string()
    .trim()
    .min(4, "Postal code must be at least 4 characters")
    .max(12),
  gst_number: z.string().trim().max(30),
  license_number: z.string().trim().max(50),
  business_type: z.string().trim().max(50),
  description: z.string().trim().max(2000),
  materials_accepted: z
    .string()
    .trim()
    .min(1, "Enter at least one accepted material, separated by commas"),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

interface DealerProfileFormProps {
  profile?: DealerProfile | null;
}

function toFormValues(profile: DealerProfile): ProfileFormValues {
  return {
    business_name: profile.business_name,
    owner_name: profile.owner_name,
    phone: profile.phone,
    email: profile.email ?? "",
    address: profile.address,
    city: profile.city,
    state: profile.state ?? "",
    postal_code: profile.postal_code,
    gst_number: profile.gst_number ?? "",
    license_number: profile.license_number ?? "",
    business_type: profile.business_type ?? "",
    description: profile.description ?? "",
    materials_accepted: profile.materials_accepted.join(", "),
  };
}

function toPayload(values: ProfileFormValues): DealerProfilePayload {
  return {
    business_name: values.business_name,
    owner_name: values.owner_name,
    phone: values.phone,
    email: values.email || null,
    address: values.address,
    city: values.city,
    state: values.state || null,
    postal_code: values.postal_code,
    gst_number: values.gst_number || null,
    license_number: values.license_number || null,
    business_type: values.business_type || null,
    description: values.description || null,
    materials_accepted: values.materials_accepted
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
  };
}

export function DealerProfileForm({ profile }: DealerProfileFormProps) {
  const isEditing = Boolean(profile);
  const createMutation = useCreateDealerProfile();
  const updateMutation = useUpdateDealerProfile();
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: profile ? toFormValues(profile) : undefined,
  });

  const mutation = isEditing ? updateMutation : createMutation;
  const isPending = mutation.isPending || isSubmitting;

  const onSubmit = async (values: ProfileFormValues) => {
    setApiError(null);
    try {
      await mutation.mutateAsync(toPayload(values));
    } catch (error) {
      setApiError(
        getApiErrorMessage(
          error,
          isEditing
            ? "Unable to update your dealer profile."
            : "Unable to create your dealer profile.",
        ),
      );
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      {apiError ? (
        <div
          role="alert"
          className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {apiError}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Business name"
          placeholder="Green Scrap Co"
          registration={register("business_name")}
          error={errors.business_name}
        />
        <FormField
          label="Owner name"
          placeholder="Full name of the owner"
          registration={register("owner_name")}
          error={errors.owner_name}
        />
        <FormField
          label="Phone"
          placeholder="+919876543210"
          registration={register("phone")}
          error={errors.phone}
        />
        <FormField
          label="Email"
          type="email"
          placeholder="business@example.com"
          registration={register("email")}
          error={errors.email}
        />
      </div>

      <FormField
        label="Address"
        placeholder="Shop number, street, locality"
        registration={register("address")}
        error={errors.address}
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <FormField
          label="City"
          placeholder="Kolkata"
          registration={register("city")}
          error={errors.city}
        />
        <FormField
          label="State"
          placeholder="West Bengal"
          registration={register("state")}
          error={errors.state}
        />
        <FormField
          label="Postal code"
          placeholder="700001"
          registration={register("postal_code")}
          error={errors.postal_code}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <FormField
          label="GST number"
          placeholder="Optional"
          registration={register("gst_number")}
          error={errors.gst_number}
        />
        <FormField
          label="License number"
          placeholder="Optional"
          registration={register("license_number")}
          error={errors.license_number}
        />
        <FormField
          label="Business type"
          placeholder="e.g. Scrap dealer"
          registration={register("business_type")}
          error={errors.business_type}
        />
      </div>

      <FormField
        label="Accepted materials (comma separated)"
        placeholder="plastic, paper, metal"
        registration={register("materials_accepted")}
        error={errors.materials_accepted}
      />

      <FormField
        label="Description"
        placeholder="A short description of your business (optional)"
        registration={register("description")}
        error={errors.description}
      />

      <Button type="submit" className="w-full sm:w-auto" disabled={isPending}>
        {isPending ? (
          <span className="flex items-center gap-2">
            <Spinner size={18} /> Saving...
          </span>
        ) : isEditing ? (
          "Save changes"
        ) : (
          "Create profile"
        )}
      </Button>
    </form>
  );
}
