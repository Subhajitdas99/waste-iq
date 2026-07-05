import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { getApiError } from "../../api/errors";
import { useAuth } from "../../hooks/useAuth";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await login(form);
      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (err) {
      setError(getApiError(err, "Login failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-8">
      <div className="glass-panel w-full max-w-md rounded-[2rem] border border-white/60 p-8 shadow-glow">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-leaf/70">Waste-IQ Access</p>
        <h1 className="mt-4 font-display text-4xl text-ink">Sign in</h1>
        <p className="mt-2 text-sm text-ink/70">Access your citizen, collector, dealer, or admin workspace.</p>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
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
            <span className="mb-2 block text-sm font-medium text-ink">Password</span>
            <input
              type="password"
              required
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              className="w-full rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 outline-none transition focus:border-leaf"
            />
          </label>

          {error ? <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-2xl bg-ink px-4 py-3 font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-sm text-ink/70">
          New to Waste-IQ?{" "}
          <Link to="/register" className="font-semibold text-leaf">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
