import { useEffect, useState } from "react";
import { MapPin, Navigation, Package, Scale, User, Weight } from "lucide-react";

import api, { getApiError } from "../../api/client";
import StatusBadge from "../../components/StatusBadge";

// ─── Action config per status ────────────────────────────────────────────
// Maps current request status -> the next action this collector can take
const NEXT_ACTION = {
  pending:    { label: "Accept request",   endpoint: (id) => `/collector/accept/${id}`,  method: "post" },
  accepted:   { label: "Start pickup",     endpoint: (id) => `/collector/start/${id}`,   method: "post" },
  on_the_way: { label: "Mark collected",   endpoint: (id) => `/collector/collect/${id}`, method: "post" },
  // "collected" needs the weight form, handled separately
};

function StatCard({ label, value, icon: Icon, color }) {
  return (
    <div className="glass-panel rounded-2xl border border-white/60 p-5 shadow-glow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-ink/40">{label}</p>
          <p className={`mt-2 font-display text-3xl ${color}`}>{value}</p>
        </div>
        <Icon className={`h-8 w-8 opacity-30 ${color}`} />
      </div>
    </div>
  );
}

function JobCard({ request, onAction, busy }) {
  const [weight, setWeight] = useState("");
  const [showWeightForm, setShowWeightForm] = useState(false);

  const action = NEXT_ACTION[request.status];
  const needsWeight = request.status === "collected";

  function submitWeight() {
    const w = Number(weight);
    if (!w || w <= 0) return;
    onAction(request.id, "/collector/complete/" + request.id, "post", { weight_kg: w });
    setShowWeightForm(false);
    setWeight("");
  }

  return (
    <div className="glass-panel rounded-3xl border border-white/60 p-5 shadow-glow space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Package className="h-4 w-4 text-leaf" />
            <h3 className="font-semibold text-ink">{request.waste_type}</h3>
            <StatusBadge status={request.status} />
          </div>
          <p className="flex items-center gap-1.5 text-sm text-ink/60">
            <User className="h-3.5 w-3.5" /> {request.citizen_name}
          </p>
          <p className="flex items-start gap-1.5 text-sm text-ink/60">
            <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {request.address}
          </p>
          {request.assignment?.weight_kg && (
            <p className="flex items-center gap-1.5 text-sm font-medium text-leaf">
              <Scale className="h-3.5 w-3.5" /> {request.assignment.weight_kg} kg collected
            </p>
          )}
        </div>
      </div>

      {/* Action button or weight form */}
      {needsWeight && !showWeightForm && (
        <button
          onClick={() => setShowWeightForm(true)}
          className="w-full rounded-2xl bg-leaf px-4 py-3 text-sm font-semibold text-sand transition hover:bg-moss"
        >
          Enter weight & complete
        </button>
      )}

      {needsWeight && showWeightForm && (
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Weight className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/30" />
            <input
              type="number" min="0.1" step="0.1" autoFocus
              placeholder="Weight (kg)"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              className="w-full rounded-2xl border border-ink/10 bg-white/80 pl-9 pr-4 py-3 text-sm outline-none focus:border-leaf"
            />
          </div>
          <button
            onClick={submitWeight}
            disabled={busy || !weight}
            className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-sand disabled:opacity-50"
          >
            {busy ? "..." : "Confirm"}
          </button>
        </div>
      )}

      {action && (
        <button
          onClick={() => onAction(request.id, action.endpoint(request.id), action.method)}
          disabled={busy}
          className="w-full rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-sand transition hover:bg-leaf disabled:cursor-not-allowed disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {request.status === "on_the_way" && <Navigation className="h-4 w-4" />}
          {busy ? "Working..." : action.label}
        </button>
      )}
    </div>
  );
}

export default function CollectorDashboard() {
  const [requests, setRequests] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [tab, setTab] = useState("open"); // "open" | "mine"

  async function loadAll() {
    setLoading(true);
    try {
      const [reqRes, summaryRes] = await Promise.all([
        api.get("/pickup-requests"),
        api.get("/collector/summary"),
      ]);
      setRequests(reqRes.data);
      setSummary(summaryRes.data);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Unable to load collector data."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAll(); }, []);

  async function handleAction(requestId, endpoint, method, payload) {
    setBusyId(requestId);
    setError("");
    try {
      await api[method](endpoint, payload);
      await loadAll();
    } catch (err) {
      setError(getApiError(err, "Action failed. Please try again."));
    } finally {
      setBusyId(null);
    }
  }

  // newest first, already sorted by backend (created_at desc) but re-sort defensively
  const sorted = [...requests].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  const open = sorted.filter((r) => r.status === "pending");
  const mine = sorted.filter((r) => r.assignment !== null);

  return (
    <div className="space-y-6">
      {/* Analytics */}
      {summary && (
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <StatCard label="Total Assigned" value={summary.total_assigned} icon={Package} color="text-ink" />
          <StatCard label="Active Jobs"    value={summary.active_jobs}    icon={Navigation} color="text-blue-600" />
          <StatCard label="Completed"      value={summary.completed_jobs} icon={Package} color="text-leaf" />
          <StatCard label="Weight Collected" value={`${summary.total_weight_kg} kg`} icon={Scale} color="text-amber-600" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-3">
        <button
          onClick={() => setTab("open")}
          className={`rounded-2xl px-5 py-2.5 text-sm font-semibold transition ${
            tab === "open" ? "bg-ink text-sand" : "border border-ink/10 bg-white/70 text-ink hover:border-leaf"
          }`}
        >
          Available ({open.length})
        </button>
        <button
          onClick={() => setTab("mine")}
          className={`rounded-2xl px-5 py-2.5 text-sm font-semibold transition ${
            tab === "mine" ? "bg-ink text-sand" : "border border-ink/10 bg-white/70 text-ink hover:border-leaf"
          }`}
        >
          My Jobs ({mine.length})
        </button>
        <button
          onClick={loadAll}
          className="ml-auto rounded-2xl border border-ink/10 bg-white/70 px-4 py-2.5 text-sm font-semibold text-ink hover:border-leaf"
        >
          Refresh
        </button>
      </div>

      {error && <p className="rounded-2xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p>}
      {loading && <p className="text-sm text-ink/60">Loading...</p>}

      {/* Open requests */}
      {tab === "open" && (
        <div className="grid gap-4 lg:grid-cols-2">
          {!loading && open.length === 0 && (
            <div className="glass-panel col-span-full rounded-[2rem] border border-white/60 p-8 text-center shadow-glow">
              <p className="font-display text-2xl text-ink">No open leads right now</p>
              <p className="mt-2 text-sm text-ink/60">Check back soon for new requests in Kolkata.</p>
            </div>
          )}
          {open.map((r) => (
            <JobCard key={r.id} request={r} onAction={handleAction} busy={busyId === r.id} />
          ))}
        </div>
      )}

      {/* My jobs */}
      {tab === "mine" && (
        <div className="grid gap-4 lg:grid-cols-2">
          {!loading && mine.length === 0 && (
            <div className="glass-panel col-span-full rounded-[2rem] border border-white/60 p-8 text-center shadow-glow">
              <p className="font-display text-2xl text-ink">No assignments yet</p>
              <p className="mt-2 text-sm text-ink/60">Accept a request from the Available tab to get started.</p>
            </div>
          )}
          {mine.map((r) => (
            <JobCard key={r.id} request={r} onAction={handleAction} busy={busyId === r.id} />
          ))}
        </div>
      )}
    </div>
  );
}