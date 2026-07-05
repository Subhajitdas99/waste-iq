import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { getApiError } from "../../api/client";
import { Skeleton } from "../../components/ui/skeleton";
import { getErrorToast, useToast } from "../../components/ui/toast";
import { useCreatePickup } from "../../hooks/usePickupRequests";

const pickupSchema = z.object({
  waste_type: z.string().trim().min(2, "Waste type must be at least 2 characters."),
  address: z.string().trim().min(8, "Pickup address must be at least 8 characters."),
  photo_url: z.preprocess(
    (value) => (typeof value === "string" ? value.trim() : value),
    z.union([z.literal(""), z.string().url("Enter a valid photo URL.")]).optional()
  ),
  latitude: z.number().min(-90, "Use My Location to set a valid latitude.").max(90),
  longitude: z.number().min(-180, "Use My Location to set a valid longitude.").max(180)
});

const defaultValues = {
  waste_type: "",
  address: "",
  photo_url: "",
  latitude: undefined,
  longitude: undefined
};

function formatCoordinate(value) {
  return typeof value === "number" ? value.toFixed(6) : "Waiting for location";
}

export default function CreatePickupForm() {
  const createPickup = useCreatePickup();
  const { toast } = useToast();
  const [successMessage, setSuccessMessage] = useState("");
  const [formError, setFormError] = useState("");
  const [locationError, setLocationError] = useState("");
  const [isLocating, setIsLocating] = useState(false);

  const {
    formState: { errors },
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

  function handleUseCurrentLocation() {
    setSuccessMessage("");
    setFormError("");
    setLocationError("");

    if (!navigator.geolocation) {
      setLocationError("Geolocation is not supported by this browser.");
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setValue("latitude", position.coords.latitude, { shouldDirty: true, shouldValidate: true });
        setValue("longitude", position.coords.longitude, { shouldDirty: true, shouldValidate: true });
        setIsLocating(false);
      },
      (error) => {
        setLocationError(error.message || "Unable to read your current location.");
        setIsLocating(false);
      },
      {
        enableHighAccuracy: true,
        maximumAge: 60_000,
        timeout: 10_000
      }
    );
  }

  async function onSubmit(values) {
    setSuccessMessage("");
    setFormError("");

    try {
      await createPickup.mutateAsync({
        waste_type: values.waste_type.trim(),
        address: values.address.trim(),
        photo_url: values.photo_url || undefined,
        latitude: values.latitude,
        longitude: values.longitude
      });

      reset(defaultValues);
      setLocationError("");
      setSuccessMessage("Pickup request created successfully.");
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
          Add the waste details, pickup address, optional photo link, and your current location.
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

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">Photo URL</span>
        <input
          type="url"
          placeholder="https://example.com/waste-photo.jpg"
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-ink outline-none transition focus:border-leaf"
          {...register("photo_url")}
        />
        {errors.photo_url ? <p className="mt-2 text-sm text-coral">{errors.photo_url.message}</p> : null}
      </label>

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
        <p className="rounded-2xl bg-leaf/10 px-4 py-3 text-sm font-medium text-leaf" role="status">
          {successMessage}
        </p>
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
        {isSubmitting ? "Creating pickup..." : "Create pickup request"}
      </button>
    </form>
  );
}
