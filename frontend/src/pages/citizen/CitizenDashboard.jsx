import { useEffect, useState } from "react";

import api, { getApiError } from "../../api/client";
import RequestCard from "../../components/RequestCard";
import StatusBadge from "../../components/StatusBadge";
import { uploadWastePhoto } from "../../utils/cloudinary";

const initialForm = {
  waste_type: "",
  address: "",
  latitude: "22.5726",
  longitude: "88.3639"
};

export default function CitizenDashboard() {
  const [requests, setRequests] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [photoFile, setPhotoFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function loadRequests() {
    setLoading(true);
    try {
      const response = await api.get("/pickup-requests");
      setRequests(response.data);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Unable to load pickup requests."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRequests();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      let photoUrl;
      if (photoFile) {
        photoUrl = await uploadWastePhoto(photoFile);
      }

      await api.post("/pickup-requests", {
        ...form,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        photo_url: photoUrl
      });

      setForm(initialForm);
      setPhotoFile(null);
      await loadRequests();
    } catch (err) {
      setError(getApiError(err, err.message || "Unable to create pickup request."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
      <section className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Create pickup</p>
        <h2 className="mt-4 font-display text-3xl text-ink">Schedule recyclable waste collection</h2>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
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

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">Waste photo</span>
            <input
              type="file"
              accept="image/*"
              onChange={(event) => setPhotoFile(event.target.files?.[0] || null)}
              className="w-full rounded-2xl border border-dashed border-ink/20 bg-white/60 px-4 py-3 text-sm text-ink/70"
            />
          </label>

          {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-2xl bg-ink px-4 py-3 font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Submitting request..." : "Create pickup request"}
          </button>
        </form>
      </section>

      <section className="space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Your requests</p>
            <h2 className="mt-2 font-display text-3xl text-ink">Pickup status board</h2>
          </div>
          <button
            type="button"
            onClick={loadRequests}
            className="rounded-2xl border border-ink/10 bg-white/70 px-4 py-3 text-sm font-semibold text-ink"
          >
            Refresh
          </button>
        </div>

        {loading ? <p className="text-sm text-ink/70">Loading pickup requests...</p> : null}

        {!loading && requests.length === 0 ? (
          <div className="glass-panel rounded-[2rem] border border-white/60 p-6 shadow-glow">
            <p className="font-display text-2xl text-ink">No requests yet</p>
            <p className="mt-2 text-sm text-ink/70">
              Your first pickup request will appear here with a live <StatusBadge status="pending" /> label.
            </p>
          </div>
        ) : null}

        <div className="space-y-5">
          {requests.map((request) => (
            <RequestCard key={request.id} request={request} />
          ))}
        </div>
      </section>
    </div>
  );
}
