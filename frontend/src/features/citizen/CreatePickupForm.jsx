import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { getApiError } from "../../api/client";
import ImageUploader from "../../components/ImageUploader";
import { Skeleton } from "../../components/ui/skeleton";
import { getErrorToast, useToast } from "../../components/ui/toast";
import { useBrowserGeolocation } from "../../hooks/useBrowserGeolocation";
import { useCreatePickup, useUpdatePickup } from "../../hooks/usePickupRequests";

const MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024;
const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"];

function isFileLike(value) {
  return (
    value &&
    typeof value === "object" &&
    typeof value.name === "string" &&
    typeof value.size === "number" &&
    typeof value.type === "string"
  );
}

const pickupSchema = z.object({
  waste_type: z.string().trim().min(2, "Waste type must be at least 2 characters."),
  address: z.string().trim().min(8, "Pickup address must be at least 8 characters."),
  image: z
    .any()
    .optional()
    .nullable()
    .refine((value) => !value || isFileLike(value), "Select a valid image file.")
    .refine((value) => !value || value.size <= MAX_IMAGE_SIZE_BYTES, "Image must be 10 MB or smaller.")
    .refine(
      (value) => !value || ACCEPTED_IMAGE_TYPES.includes(value.type),
      "Image must be jpg, jpeg, png, or webp."
    ),
  latitude: z.number().min(-90, "Use My Location to set a valid latitude.").max(90),
  longitude: z.number().min(-180, "Use My Location to set a valid longitude.").max(180)
});

const defaultValues = {
  waste_type: "",
  address: "",
  image: null,
  latitude: undefined,
  longitude: undefined
};

function formatCoordinate(value) {
  return typeof value === "number" ? value.toFixed(6) : "Waiting for location";
}

export default function CreatePickupForm() {
  const createPickup = useCreatePickup();
  const updatePickup = useUpdatePickup();
  const { toast } = useToast();
  const [successMessage, setSuccessMessage] = useState("");
  const [uploadedImageUrl, setUploadedImageUrl] = useState("");
  const [createdRequest, setCreatedRequest] = useState(null);
  const [isAiResolved, setIsAiResolved] = useState(false);
  const [formError, setFormError] = useState("");
  const {
    error: locationError,
    isLocating,
    position,
    requestLocation
  } = useBrowserGeolocation({
    errorTitle: "Pickup location unavailable"
  });

  const {
    formState: { errors },
    control,
    handleSubmit,
    register,
    reset,
    setValue,
    watch
  } = useForm({
    resolver: zodResolver(pickupSchema),
    defaultValues
  });

  const latitude = watch("latitude");
  const longitude = watch("longitude");
  const isSubmitting = createPickup.isPending;

  useEffect(() => {
    if (!position) {
      return;
    }

    setValue("latitude", position.latitude, { shouldDirty: true, shouldValidate: true });
    setValue("longitude", position.longitude, { shouldDirty: true, shouldValidate: true });
  }, [position, setValue]);

  function handleUseCurrentLocation() {
    setSuccessMessage("");
    setUploadedImageUrl("");
    setFormError("");
    setCreatedRequest(null);
    setIsAiResolved(false);
    requestLocation();
  }

  async function onSubmit(values) {
    setSuccessMessage("");
    setUploadedImageUrl("");
    setFormError("");
    setCreatedRequest(null);
    setIsAiResolved(false);

    try {
      const formData = new FormData();
      formData.append("waste_type", values.waste_type.trim());
      formData.append("address", values.address.trim());
      formData.append("latitude", values.latitude);
      formData.append("longitude", values.longitude);

      if (values.image) {
        formData.append("image", values.image);
      }

      const response = await createPickup.mutateAsync(formData);

      reset(defaultValues);
      setSuccessMessage("Pickup request created successfully.");
      setCreatedRequest(response);
      if (response && response.image_url) {
        setUploadedImageUrl(response.image_url);
      }
      toast({
        title: "Pickup created",
        description: "Your pickup request has been submitted successfully.",
        variant: "success"
      });
    } catch (error) {
      setFormError(getApiError(error, "Unable to create pickup request."));
      toast(getErrorToast(error, "Unable to create pickup request."));
    }
  }

  async function handleAcceptPrediction() {
    setIsAiResolved(true);
    toast({
      title: "Prediction Accepted",
      description: "The AI classification has been confirmed.",
      variant: "success"
    });
  }

  async function handleOverrideCategory(newCategory) {
    if (!newCategory || !createdRequest) return;
    try {
      await updatePickup.mutateAsync({
        id: createdRequest.id,
        payload: { waste_type: newCategory }
      });
      setIsAiResolved(true);
      toast({
        title: "Category Updated",
        description: `Waste type has been manually set to ${newCategory}.`,
        variant: "success"
      });
    } catch (error) {
      toast(getErrorToast(error, "Failed to update category."));
    }
  }

  function handleInvalidSubmit() {
    toast({
      title: "Validation error",
      description: "Please fix the highlighted fields before creating a pickup.",
      variant: "error"
    });
  }

  return (
    <form className="glass-panel space-y-5 p-6" onSubmit={handleSubmit(onSubmit, handleInvalidSubmit)}>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-moss">Create Pickup</p>
        <h2 className="mt-2 text-2xl font-bold text-ink">Schedule a new waste pickup</h2>
        <p className="mt-2 text-sm text-ink/60">
          Add the waste details, pickup address, optional photo, and your current location.
        </p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">Waste Type</span>
        <input
          type="text"
          placeholder="Plastic bottles, cardboard, e-waste"
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-ink outline-none transition focus:border-leaf"
          {...register("waste_type")}
        />
        {errors.waste_type ? <p className="mt-2 text-sm text-coral">{errors.waste_type.message}</p> : null}
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">Pickup Address</span>
        <textarea
          rows="4"
          placeholder="House number, street, landmark, city"
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-ink outline-none transition focus:border-leaf"
          {...register("address")}
        />
        {errors.address ? <p className="mt-2 text-sm text-coral">{errors.address.message}</p> : null}
      </label>

      <Controller
        name="image"
        control={control}
        render={({ field }) => (
          <ImageUploader
            name={field.name}
            value={field.value}
            onChange={field.onChange}
            onBlur={field.onBlur}
            error={errors.image?.message}
            disabled={isSubmitting}
          />
        )}
      />

      <div className="rounded-3xl border border-ink/10 bg-white/60 p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-ink">Pickup Location</p>
            <p className="text-sm text-ink/60">Use your browser location to populate latitude and longitude.</p>
          </div>
          <button
            type="button"
            onClick={handleUseCurrentLocation}
            disabled={isLocating || isSubmitting}
            className="rounded-2xl bg-leaf px-4 py-3 text-sm font-semibold text-sand transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLocating ? "Finding location..." : "Use My Location"}
          </button>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl bg-sand/70 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-moss">Latitude</p>
            {isLocating ? (
              <Skeleton className="mt-2 h-5 w-28 rounded-full bg-ink/10" />
            ) : (
              <p className="mt-1 font-semibold text-ink">{formatCoordinate(latitude)}</p>
            )}
          </div>
          <div className="rounded-2xl bg-sand/70 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-moss">Longitude</p>
            {isLocating ? (
              <Skeleton className="mt-2 h-5 w-28 rounded-full bg-ink/10" />
            ) : (
              <p className="mt-1 font-semibold text-ink">{formatCoordinate(longitude)}</p>
            )}
          </div>
        </div>

        {errors.latitude || errors.longitude ? (
          <p className="mt-3 text-sm text-coral">Use My Location before submitting this pickup request.</p>
        ) : null}
        {locationError ? <p className="mt-3 text-sm text-coral">{locationError}</p> : null}
      </div>

      {successMessage ? (
        <div className="space-y-4">
          <p className="rounded-2xl bg-leaf/10 px-4 py-3 text-sm font-medium text-leaf" role="status">
            {successMessage}
          </p>
          {uploadedImageUrl ? (
            <div className="rounded-2xl border border-ink/10 bg-white/60 p-4">
              <p className="mb-2 text-sm font-semibold text-ink">Uploaded Image</p>
              <img
                src={`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}${uploadedImageUrl}`}
                alt="Uploaded pickup"
                className="max-h-48 rounded-xl object-cover"
              />
              {createdRequest?.category && !isAiResolved && (
                <div className="mt-4 border-t border-ink/10 pt-4">
                  <p className="text-sm font-semibold text-ink">AI Classification</p>
                  <p className="text-sm text-ink/60">
                    Detected Waste: <span className="font-semibold">{createdRequest.category}</span>
                    <br />
                    Confidence: <span className="font-semibold">{Math.round((createdRequest.confidence || 0) * 100)}%</span>
                  </p>
                  
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handleAcceptPrediction}
                      className="rounded-xl bg-leaf px-3 py-2 text-xs font-semibold text-sand transition hover:bg-ink"
                    >
                      Accept Prediction
                    </button>
                    <select
                      className="rounded-xl border border-ink/10 bg-white/80 px-3 py-2 text-xs text-ink outline-none transition focus:border-leaf"
                      onChange={(e) => handleOverrideCategory(e.target.value)}
                      defaultValue=""
                    >
                      <option value="" disabled>Select another category</option>
                      <option value="Plastic">Plastic</option>
                      <option value="Paper">Paper</option>
                      <option value="Glass">Glass</option>
                      <option value="Metal">Metal</option>
                      <option value="Cardboard">Cardboard</option>
                      <option value="E-Waste">E-Waste</option>
                      <option value="Battery">Battery</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      ) : null}
      {formError ? (
        <p className="rounded-2xl bg-coral/10 px-4 py-3 text-sm font-medium text-coral" role="alert">
          {formError}
        </p>
      ) : null}

      {isSubmitting ? (
        <div className="rounded-2xl bg-white/60 p-4">
          <Skeleton className="h-4 w-40 rounded-full bg-leaf/15" />
          <Skeleton className="mt-3 h-3 w-full rounded-full" />
        </div>
      ) : null}

      <button
        type="submit"
        disabled={isSubmitting || isLocating}
        className="w-full rounded-2xl bg-ink px-4 py-3 font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? (watch("image") ? "Uploading..." : "Creating pickup...") : "Create pickup request"}
      </button>
    </form>
  );
}
