import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getApiError } from "../../api/client";
import { useAuth } from "../../hooks/useAuth";

const roleOptions = [
  { value: "citizen", label: "Citizen" },
  { value: "collector", label: "Collector" },
  { value: "dealer", label: "Dealer" },
  { value: "admin", label: "Admin" }
];

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    role: "citizen",
    admin_code: ""
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await register(form);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(getApiError(err, "Registration failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-8">
      <div className="glass-panel w-full max-w-2xl rounded-[2rem] border border-white/60 p-8 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Launch Kolkata</p>
        <h1 className="mt-4 font-display text-4xl text-ink">Create your Waste-IQ account</h1>

        <form className="mt-8 grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
          <label className="block sm:col-span-2">
            <span className="mb-2 block text-sm font-medium text-ink">Full name</span>
            <input
              type="text"
              required
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">Email</span>
            <input
              type="email"
              required
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
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
            <span className="mb-2 block text-sm font-medium text-ink">Password</span>
            <input
              type="password"
              required
              minLength={8}
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-ink">Role</span>
            <select
              value={form.role}
              onChange={(event) => setForm({ ...form, role: event.target.value })}
              className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
            >
              {roleOptions.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </label>

          {form.role === "admin" ? (
            <label className="block sm:col-span-2">
              <span className="mb-2 block text-sm font-medium text-ink">Admin registration code</span>
              <input
                type="text"
                value={form.admin_code}
                onChange={(event) => setForm({ ...form, admin_code: event.target.value })}
                className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
              />
            </label>
          ) : null}

          {error ? <p className="sm:col-span-2 rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

          <button
            type="submit"
            disabled={submitting}
            className="sm:col-span-2 rounded-2xl bg-ink px-4 py-3 font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-sm text-ink/70">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-leaf">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
