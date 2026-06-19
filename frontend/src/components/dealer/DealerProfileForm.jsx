import { useEffect, useState } from "react";

function buildInitialForm(profile) {
  return {
    business_name: profile?.business_name || "",
    owner_name: profile?.owner_name || "",
    phone: profile?.phone || "",
    address: profile?.address || "",
    city: profile?.city || "",
    pincode: profile?.pincode || "",
    gst_number: profile?.gst_number || "",
    license_number: profile?.license_number || "",
    materials_accepted: profile?.materials_accepted?.join(", ") || ""
  };
}

export default function DealerProfileForm({ profile, submitting, onSubmit }) {
  const [form, setForm] = useState(() => buildInitialForm(profile));

  useEffect(() => {
    setForm(buildInitialForm(profile));
  }, [profile]);

  function handleSubmit(event) {
    event.preventDefault();

    const payload = {
      ...form,
      gst_number: form.gst_number || null,
      license_number: form.license_number || null,
      materials_accepted: form.materials_accepted
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
    };

    onSubmit(payload);
  }

  return (
    <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">Business name</span>
        <input
          type="text"
          required
          value={form.business_name}
          onChange={(event) => setForm({ ...form, business_name: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">Owner name</span>
        <input
          type="text"
          required
          value={form.owner_name}
          onChange={(event) => setForm({ ...form, owner_name: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">Phone</span>
        <input
          type="text"
          required
          value={form.phone}
          onChange={(event) => setForm({ ...form, phone: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">City</span>
        <input
          type="text"
          required
          value={form.city}
          onChange={(event) => setForm({ ...form, city: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">Pincode</span>
        <input
          type="text"
          required
          value={form.pincode}
          onChange={(event) => setForm({ ...form, pincode: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-ink">GST number</span>
        <input
          type="text"
          value={form.gst_number}
          onChange={(event) => setForm({ ...form, gst_number: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <label className="block sm:col-span-2">
        <span className="mb-2 block text-sm font-medium text-ink">License number</span>
        <input
          type="text"
          value={form.license_number}
          onChange={(event) => setForm({ ...form, license_number: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <label className="block sm:col-span-2">
        <span className="mb-2 block text-sm font-medium text-ink">Business address</span>
        <textarea
          required
          rows="4"
          value={form.address}
          onChange={(event) => setForm({ ...form, address: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <label className="block sm:col-span-2">
        <span className="mb-2 block text-sm font-medium text-ink">Materials accepted</span>
        <textarea
          required
          rows="3"
          placeholder="Plastic, paper, cardboard, e-waste"
          value={form.materials_accepted}
          onChange={(event) => setForm({ ...form, materials_accepted: event.target.value })}
          className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
        />
      </label>

      <button
        type="submit"
        disabled={submitting}
        className="sm:col-span-2 rounded-2xl bg-ink px-4 py-3 font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "Saving profile..." : profile ? "Update dealer profile" : "Create dealer profile"}
      </button>
    </form>
  );
}
