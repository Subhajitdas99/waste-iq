import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle2, MapPin, Sparkles } from "lucide-react";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SeoHead } from "@/components/seo/SeoHead";
import { PageHeader } from "@/components/PageHeader";
import { DashboardCard } from "@/components/dashboard/DashboardCard";
import { ImageUploader } from "@/components/dashboard/ImageUploader";
import { useBrowserGeolocation } from "@/hooks/useBrowserGeolocation";
import { useCreateCitizenPickup } from "@/hooks/useCitizenPickups";
import { getApiErrorMessage } from "@/lib/api-error";
import { formatDateTime, formatWeight } from "@/lib/pickup";
import type { PickupRequest } from "@/types/pickup";

const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;
const MAX_NOTES_LENGTH = 2000;
const MAX_ESTIMATED_WEIGHT_KG = 10000;

function isFile(value: unknown): value is File {
  return typeof File !== "undefined" && value instanceof File;
}

const pickupSchema = z.object({
  waste_type: z.string().trim().min(2, "Waste type must be at least 2 characters."),
  address: z.string().trim().min(8, "Pickup address must be at least 8 characters."),
  latitude: z.coerce.number().min(-90).max(90),
  longitude: z.coerce.number().min(-180).max(180),
  estimated_weight_kg: z
    .preprocess(
      (value) =>
        typeof value === "number" && Number.isFinite(value) ? value : undefined,
      z
        .number({ invalid_type_error: "Enter a valid estimated weight in kilograms." })
        .min(0.1, "Estimated weight must be at least 0.1 kg.")
        .max(MAX_ESTIMATED_WEIGHT_KG, "Estimated weight cannot exceed 10,000 kg.")
        .optional(),
    ),
  preferred_time: z
    .string()
    .optional()
    .transform((value) => (value ? value : undefined))
    .refine(
      (value) => !value || !Number.isNaN(Date.parse(value)),
      "Enter a valid date and time.",
    )
    .refine(
      (value) => !value || Date.parse(value) > Date.now(),
      "Preferred time must be in the future.",
    ),
  notes: z
    .string()
    .trim()
    .max(MAX_NOTES_LENGTH, "Notes must be 2,000 characters or fewer.")
    .optional(),
  image: z
    .custom<File | null | undefined>(
      (value) => value === null || value === undefined || isFile(value),
      "Select a valid image file.",
    )
    .refine(
      (value) => !isFile(value) || value.size <= MAX_FILE_SIZE,
      "Image must be 10 MB or smaller.",
    )
    .refine(
      (value) => !isFile(value) || ACCEPTED_IMAGE_TYPES.includes(value.type),
      "Accepted formats are JPG, JPEG, PNG, and WEBP.",
    )
    .optional(),
});

type PickupFormValues = z.infer<typeof pickupSchema>;

const defaultValues: PickupFormValues = {
  waste_type: "",
  address: "",
  latitude: Number.NaN,
  longitude: Number.NaN,
  estimated_weight_kg: undefined,
  preferred_time: "",
  notes: "",
  image: null,
};

const steps = [
  {
    title: "Material",
    description: "Describe the recyclable waste and add an optional photo for AI preview.",
    fields: ["waste_type", "image"] as const,
  },
  {
    title: "Location & Details",
    description: "Add the pickup address, estimated weight, preferred time, and any notes.",
    fields: [
      "address",
      "latitude",
      "longitude",
      "estimated_weight_kg",
      "preferred_time",
      "notes",
    ] as const,
  },
  {
    title: "Review",
    description: "Confirm the exact payload that will be sent to the backend.",
    fields: [] as const,
  },
];

export function NewPickupPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [successPickup, setSuccessPickup] = useState<PickupRequest | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const geolocation = useBrowserGeolocation();
  const createPickupMutation = useCreateCitizenPickup();

  const {
    control,
    handleSubmit,
    register,
    setValue,
    trigger,
    watch,
    reset,
    formState: { errors },
  } = useForm<PickupFormValues>({
    resolver: zodResolver(pickupSchema),
    defaultValues,
  });

  const values = watch();
  const isSubmitting = createPickupMutation.isPending;

  useEffect(() => {
    if (!geolocation.position) {
      return;
    }

    setValue("latitude", geolocation.position.latitude, { shouldValidate: true });
    setValue("longitude", geolocation.position.longitude, { shouldValidate: true });
  }, [geolocation.position, setValue]);

  const goToNextStep = async () => {
    const isValid = await trigger(steps[currentStep].fields);
    if (isValid) {
      setCurrentStep((step) => Math.min(step + 1, steps.length - 1));
    }
  };

  const onSubmit = async (formValues: PickupFormValues) => {
    setApiError(null);
    setUploadProgress(0);

    try {
      const createdPickup = await createPickupMutation.mutateAsync({
        payload: {
          waste_type: formValues.waste_type,
          address: formValues.address,
          latitude: formValues.latitude,
          longitude: formValues.longitude,
          estimated_weight_kg: formValues.estimated_weight_kg ?? null,
          preferred_time: formValues.preferred_time ?? null,
          notes: formValues.notes ?? null,
          image: formValues.image ?? null,
        },
        onUploadProgress: setUploadProgress,
      });

      setSuccessPickup(createdPickup);
      setCurrentStep(0);
      setUploadProgress(0);
      reset(defaultValues);
    } catch (error) {
      setApiError(getApiErrorMessage(error, "Unable to create pickup request."));
    }
  };

  const aiPreviewIsAvailable =
    Boolean(successPickup?.category) &&
    successPickup?.category !== "Unknown" &&
    (successPickup?.confidence ?? 0) > 0;

  return (
    <>
      <SeoHead
        title="Create Pickup"
        description="Create a new Waste-IQ pickup request with weight, preferred time, notes, and image upload."
        path="/dashboard/pickups/new"
      />

      <PageHeader
        title="Create Pickup Request"
        description="This multi-step flow submits the full Sprint 5 citizen contract: material, location, scheduling, and photo."
        actions={
          <Button asChild variant="outline">
            <Link to="/dashboard/pickups">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Pickups
            </Link>
          </Button>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <DashboardCard
          title={steps[currentStep].title}
          description={steps[currentStep].description}
          className="min-h-[32rem]"
        >
          <div className="mb-8 grid gap-3 md:grid-cols-3">
            {steps.map((step, index) => (
              <div
                key={step.title}
                className={`rounded-2xl border px-4 py-3 text-sm ${
                  index === currentStep
                    ? "border-primary/20 bg-primary/10 text-primary"
                    : index < currentStep
                      ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                      : "border-border bg-muted/30 text-muted-foreground"
                }`}
              >
                <p className="text-xs uppercase tracking-[0.2em]">Step {index + 1}</p>
                <p className="mt-1 font-semibold">{step.title}</p>
              </div>
            ))}
          </div>

          {successPickup ? (
            <div
              role="status"
              className="mb-6 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300"
            >
              Pickup request #{successPickup.id} was created successfully.
            </div>
          ) : null}

          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            {currentStep === 0 ? (
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="waste_type">Waste Type</Label>
                  <Input
                    id="waste_type"
                    placeholder="Plastic bottles, cardboard, mixed paper"
                    {...register("waste_type")}
                  />
                  {errors.waste_type ? (
                    <p className="text-sm text-destructive">{errors.waste_type.message}</p>
                  ) : null}
                </div>

                <Controller
                  name="image"
                  control={control}
                  render={({ field }) => (
                    <ImageUploader
                      value={(field.value as File | null | undefined) ?? null}
                      onChange={field.onChange}
                      error={errors.image?.message}
                      disabled={isSubmitting}
                      uploadProgress={uploadProgress}
                    />
                  )}
                />
              </div>
            ) : null}

            {currentStep === 1 ? (
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="address">Pickup Address</Label>
                  <textarea
                    id="address"
                    rows={4}
                    placeholder="Street address, area, city, and any location clarifier."
                    className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    {...register("address")}
                  />
                  {errors.address ? (
                    <p className="text-sm text-destructive">{errors.address.message}</p>
                  ) : null}
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="estimated_weight_kg">Estimated Weight (kg)</Label>
                    <Input
                      id="estimated_weight_kg"
                      type="number"
                      min="0.1"
                      max={MAX_ESTIMATED_WEIGHT_KG}
                      step="any"
                      placeholder="e.g. 4.5"
                      {...register("estimated_weight_kg", { valueAsNumber: true })}
                    />
                    {errors.estimated_weight_kg ? (
                      <p className="text-sm text-destructive">
                        {errors.estimated_weight_kg.message}
                      </p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="preferred_time">Preferred Pickup Time</Label>
                    <Input
                      id="preferred_time"
                      type="datetime-local"
                      {...register("preferred_time")}
                    />
                    {errors.preferred_time ? (
                      <p className="text-sm text-destructive">{errors.preferred_time.message}</p>
                    ) : null}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notes">Notes (optional)</Label>
                  <textarea
                    id="notes"
                    rows={3}
                    maxLength={MAX_NOTES_LENGTH}
                    placeholder="Landmark details, gate instructions, or special handling requests."
                    className="flex min-h-[90px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    {...register("notes")}
                  />
                  {errors.notes ? (
                    <p className="text-sm text-destructive">{errors.notes.message}</p>
                  ) : null}
                </div>

                <div className="rounded-3xl border bg-muted/20 p-5">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-semibold">Use current location</p>
                      <p className="text-sm text-muted-foreground">
                        Fill latitude and longitude from the browser when available.
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      className="gap-2"
                      onClick={geolocation.requestLocation}
                      disabled={geolocation.isLocating}
                    >
                      <MapPin className="h-4 w-4" />
                      {geolocation.isLocating ? "Detecting..." : "Use My Location"}
                    </Button>
                  </div>

                  {geolocation.error ? (
                    <p className="mt-3 text-sm text-destructive">{geolocation.error}</p>
                  ) : null}

                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="latitude">Latitude</Label>
                      <Input
                        id="latitude"
                        type="number"
                        step="any"
                        {...register("latitude", { valueAsNumber: true })}
                      />
                      {errors.latitude ? (
                        <p className="text-sm text-destructive">Enter a valid latitude.</p>
                      ) : null}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="longitude">Longitude</Label>
                      <Input
                        id="longitude"
                        type="number"
                        step="any"
                        {...register("longitude", { valueAsNumber: true })}
                      />
                      {errors.longitude ? (
                        <p className="text-sm text-destructive">Enter a valid longitude.</p>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            {currentStep === 2 ? (
              <div className="space-y-4">
                <div className="rounded-3xl border bg-muted/20 p-5">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                    Backend Payload Preview
                  </p>
                  <dl className="mt-4 grid gap-4 md:grid-cols-2">
                    <div>
                      <dt className="text-sm text-muted-foreground">Waste Type</dt>
                      <dd className="mt-1 font-medium">{values.waste_type}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-muted-foreground">Image</dt>
                      <dd className="mt-1 font-medium">
                        {values.image ? values.image.name : "No image selected"}
                      </dd>
                    </div>
                    <div className="md:col-span-2">
                      <dt className="text-sm text-muted-foreground">Address</dt>
                      <dd className="mt-1 font-medium">{values.address}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-muted-foreground">Estimated Weight</dt>
                      <dd className="mt-1 font-medium">
                        {formatWeight(values.estimated_weight_kg)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm text-muted-foreground">Preferred Time</dt>
                      <dd className="mt-1 font-medium">
                        {values.preferred_time
                          ? formatDateTime(values.preferred_time)
                          : "No preferred time"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm text-muted-foreground">Latitude</dt>
                      <dd className="mt-1 font-medium">{values.latitude}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-muted-foreground">Longitude</dt>
                      <dd className="mt-1 font-medium">{values.longitude}</dd>
                    </div>
                    <div className="md:col-span-2">
                      <dt className="text-sm text-muted-foreground">Notes</dt>
                      <dd className="mt-1 font-medium">
                        {values.notes?.trim() ? values.notes : "No notes provided"}
                      </dd>
                    </div>
                  </dl>
                </div>

                {apiError ? (
                  <div
                    role="alert"
                    className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
                  >
                    {apiError}
                  </div>
                ) : null}
              </div>
            ) : null}

            <div className="flex flex-col gap-3 border-t pt-6 sm:flex-row sm:justify-between">
              <Button
                type="button"
                variant="outline"
                onClick={() => setCurrentStep((step) => Math.max(step - 1, 0))}
                disabled={currentStep === 0 || isSubmitting}
              >
                Back
              </Button>

              {currentStep < steps.length - 1 ? (
                <Button type="button" onClick={goToNextStep}>
                  Next Step
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              ) : (
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Submitting..." : "Create Pickup Request"}
                </Button>
              )}
            </div>
          </form>
        </DashboardCard>

        <div className="space-y-6">
          <DashboardCard
            title="Supported Request Fields"
            description="Every field in this form maps to the FastAPI citizen pickup contract."
          >
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li>`waste_type` and `address`</li>
              <li>`latitude` / `longitude` (browser geolocation)</li>
              <li>`estimated_weight_kg` — optional, 0.1–10,000 kg</li>
              <li>`preferred_time` — optional future datetime</li>
              <li>`notes` — optional, up to 2,000 characters</li>
              <li>`image` (multipart upload on create)</li>
            </ul>
          </DashboardCard>

          <DashboardCard
            title="AI Image Preview"
            description="Photos are analyzed on upload and the result is stored with the request."
          >
            <div className="flex items-start gap-3">
              <div className="rounded-2xl bg-primary/10 p-3 text-primary">
                <Sparkles className="h-5 w-5" />
              </div>
              <div className="text-sm text-muted-foreground">
                <p>
                  The classifier returns a material category and confidence score. The model is
                  currently on standby, so uploaded photos return{" "}
                  <span className="font-medium">Unknown</span> with{" "}
                  <span className="font-medium">0%</span> confidence until the inference service
                  is deployed.
                </p>
                <p className="mt-2">
                  Once live, the detected category and confidence appear in the success panel and
                  on the pickup details page.
                </p>
              </div>
            </div>
          </DashboardCard>

          {successPickup ? (
            <DashboardCard
              title="Success"
              description="Open the pickup details page to follow collector progress and timeline updates."
            >
              <div className="rounded-2xl border bg-muted/20 p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 text-primary" />
                  <div>
                    <p className="font-medium">Request #{successPickup.id} created</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Your pickup is now in the citizen queue with status{" "}
                      <span className="font-medium">{successPickup.status}</span>.
                    </p>
                  </div>
                </div>

                <div className="mt-4 rounded-2xl border border-dashed bg-background/60 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                    AI Image Preview
                  </p>
                  {aiPreviewIsAvailable ? (
                    <p className="mt-2 text-sm font-medium">
                      Detected material: {successPickup?.category} (
                      {((successPickup?.confidence ?? 0) * 100).toFixed(0)}% confidence)
                    </p>
                  ) : (
                    <p className="mt-2 text-sm text-muted-foreground">
                      {successPickup?.image_url
                        ? "Photo stored with the request. Classification preview activates when the AI model is live."
                        : "No photo attached to this request, so there is nothing to classify."}
                    </p>
                  )}
                </div>

                <Button asChild className="mt-4 w-full">
                  <Link to={`/dashboard/pickups/${successPickup.id}`}>View Pickup Details</Link>
                </Button>
              </div>
            </DashboardCard>
          ) : null}
        </div>
      </div>
    </>
  );
}
