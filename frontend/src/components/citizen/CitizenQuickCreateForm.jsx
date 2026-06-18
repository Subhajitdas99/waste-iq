import { useState } from "react";

import { getApiError } from "../../api/client";
import { createPickupRequest } from "../../api/pickupRequests";
import { uploadWastePhoto } from "../../utils/cloudinary";

const initialForm = {
  waste_type: "",
  address: "",
  latitude: "22.5726",
  longitude: "88.3639"
};

export default function CitizenQuickCreateForm({ onCreated }) {
  const [form, setForm] = useState(initialForm);
  const [photoFile, setPhotoFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      let photoUrl;
      if (photoFile) {
        photoUrl = await uploadWastePhoto(photoFile);
      }

      await createPickupRequest({
        ...form,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        photo_url: photoUrl
      });

      setForm(initialForm);
      setPhotoFile(null);
      await onCreated?.();
    } catch (err) {
      setError(getApiError(err, err.message || "Unable to create pickup request."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div className="grid gap-4 lg:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-ink">Waste type</span>
          <input
            type="text"
            required
            placeholder="Plastic bottles, cardboard, e-waste"
            value={form.waste_type}
            onChange={(event) => setForm({ ...form, waste_type: event.target.value })}
            className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-ink">Waste photo</span>
          <input
            type="file"
            accept="image/*"
            onChange={(event) => setPhotoFile(event.target.files?.[0] || null)}
            className="w-full rounded-2xl border border-dashed border-ink/20 bg-white/60 px-4 py-3 text-sm text-ink/70"
          />
        </label>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">Pickup address</span>
        <textarea
          required
          rows="4"
          value={form.address}
          onChange={(event) => setForm({ ...form, address: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-ink">Latitude</span>
          <input
            type="number"
            step="0.0001"
            required
            value={form.latitude}
            onChange={(event) => setForm({ ...form, latitude: event.target.value })}
            className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-ink">Longitude</span>
          <input
            type="number"
            step="0.0001"
            required
            value={form.longitude}
            onChange={(event) => setForm({ ...form, longitude: event.target.value })}
            className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
          />
        </label>
      </div>

      {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-2xl bg-ink px-4 py-3 font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Submitting request..." : "Create pickup request"}
      </button>
    </form>
  );
}
